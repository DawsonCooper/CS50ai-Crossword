import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [ 
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        # loops over our domains which will be Variable objects linked to a set which is our possible words
        for word in self.domains:
            newDomain = set()
            # loop over the domain for our variable and create a new set of words that match our variables length
            for item in self.domains[word]:
                if len(item) == word.length:
                    newDomain.add(item)
            self.domains[word] = newDomain

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # check if the variables overlap
        
        oL = self.crossword.overlaps[x, y]
        # if they do not overlap then return false
        if oL == None:
            return False     
        # loop over x domain 
        newDomain = set()
        for word in self.domains[x]:
            xoL = word[oL[0]]
            for word2 in self.domains[y]:
                if xoL == word2[oL[1]]:
                    newDomain.add(word)
        if self.domains[x] == newDomain:
            return False
        else:
            self.domains[x] = newDomain
            return True


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.

        
        """

        overlaps = self.crossword.overlaps
        print({"overlaps": overlaps})
        if arcs != None:
            queue = arcs

        else:
            # create a queue of all arcs
            queue = []
            # loop over our overlaps and as long as the value is not None we will want to add it to the queue
            for item in overlaps:
                if overlaps[item] != None:
                    queue.append(item)
        # loop over our queue if its not empty remove the first value and revise it (we will want to add back arcs but which ones???)
        while queue:
            arc = queue.pop(0)   
            x, y = arc[0], arc[1]    
            revised = self.revise(x,y)
            if revised:
                # changes have been made to x's domain we will want to make sure it still has words in it 
                if len(self.domains[x]) == 0:
                    return False
                # we will want to now double check all arcs that are linked to x to see if any more changes can be made 
                for xArcs in overlaps:
                    if xArcs[0] == x:
                        queue.append(xArcs)
        return True
            

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        #TODO: we may want to loop over our crossword.varaibles to check if any are excluded from our assignment
        for item in self.crossword.variables:
            if item not in assignment:
                return False
        
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        print({"assignment":assignment})
        history = []
        # make sure all values are unique

        for item in assignment:
            if assignment[item] in history:
                print('False1')
                return False
            history.append(assignment[item])
        # make sure all values are the correct length

            if len(assignment[item]) != item.length:

                print('False2')
                return False
        # make sure all values are arc consistent
            itemArcs = []
            for oL in self.crossword.overlaps:
                if oL[0] == item and self.crossword.overlaps[oL] != None:
                    itemArcs.append(oL)
            
            for arc in itemArcs:   
                # arc = {(var1, var2): (xIndex, yIndex)}
                xIndex = self.crossword.overlaps[arc][0]
                yIndex = self.crossword.overlaps[arc][1]
                # if the variable that we are intersecting with is not in our assigment list 
                if arc[1] not in assignment:
                    continue
                # if our intersection is already assigned to a value we will want to make sure our word we are testing does not conflict with it
                else:
                    if assignment[item][xIndex] != assignment[arc[1]][yIndex]:
                        print('False3')
                        return False
        print('True')
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.

        var is a variable object
        assignment is a dictionary of variables and their assigned values
        if one of our neighbors is in assignment we will want to ignore it
        """
        domain = self.domains[var]
        neighbors = []
        class RankItem:
            def __init__(self, word, change):
                self.word = word
                self.change = change
        domainRank = []
        # get all overlaps where the overlapping variable is not in assignment and the values != None
        for item in self.crossword.overlaps:
            if item[0] == var and item[1] not in assignment and self.crossword.overlaps[item] != None:
                neighbors.append(item[1])
        # for each value in our domain we will want to check how many values it rules out for each neighbor inseting the values into our domain rank list as a RankItem
        for word in domain:
            count = 0 
            for neighbor in neighbors:
                if word in self.domains[neighbor]:
                    count += 1
            domainRank.append(RankItem(word, count))
        print({"domainRank": domainRank})
        
        # sort our domain rank list by the change value and return a list of the words once sorted
        domainRank.sort(key = lambda item: item.change)
        sortedDomain = [item.word for item in domainRank]
        print({"sortedDomain":sortedDomain})
        return sortedDomain         
        

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # create a list of all of our unassigned variables
        unassignedVars = []
        for item in self.crossword.variables:
            if item not in assignment:
                unassignedVars.append(item)
        # sort our unassigned variable list by the length of their domain
        unassignedVars.sort(key = lambda item: len(self.domains[item]))
        print({"unassignedVars":unassignedVars})
        return unassignedVars[0]
        

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # if none ouf our assignment variable are unassigned then we will want to return our assignment
        if self.assignment_complete(assignment):
            return assignment
        # select one of our unassigned variables
        var = self.select_unassigned_variable(assignment)

        def getOverlaps(var):
            overlaps = []
            for item in self.crossword.overlaps:
                if item[0] == var and self.crossword.overlaps[item] != None and item[1] not in assignment:
                    overlaps.append(item)
            return overlaps

        for item in self.order_domain_values(var, assignment):
            assignment[var] = item
            if self.consistent(assignment):
                print({'neighbor':self.crossword.neighbors(var)})
                # get all overlaps for var that are not in assignment and add call ac3 on them
                self.ac3(getOverlaps(var))
                result = self.backtrack(assignment)
                if result != None:
                    return result
            del assignment[var]
        return None

                


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
