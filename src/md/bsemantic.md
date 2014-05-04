![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

A framework to translate meaning into symbols, and infer meaning from symbols, using a customizable ruleset.

## Preamble

"What's in a name ?" - one could say, and answer everything and nothing. A name itself is just a *sequence of characters*, and what makes it useful is the meaning we assign to those as a whole. If you take many of those sequences, lets call them *symbol* from now on, and place them in a specific order, they gain context which further defines their meaning - its a *sentence*.

For pipeline tool development, names used to playing a major roles, as they contain a lot of information and meaning that can be used to perform tasks. Meaning may be transformed as well, which generates a new name.

If code interacts with names, it usually has to either build those *symbols* that it believes belong to a meaning that it wants to express, or it tries to analyze the its characters to figure out its meaning, or the *symbols* in sentences to find out even more.

Doing so will of course make it very dependent on the actual character values, or the context of multiple concatenated *symbols*. This tends to be very problematic as they are prone to change, and sometimes they are required to change to adapt to changed requirements. 

In the end, what code is interested in is not the *symbol* itself, but the meaning that it bears, and we seek a way to decouple those so that the symbol can change, as long as the meaning doesn't.

## Semantic Name Handling

The solution to the inherent inflexibility of using *symbols* directly is to not actually do it. The only thing we want to and can keep static is the semantic aspect of a symbol, i.e. the meaning.

Code will not directly interact with names as strings, or with *symbols* in *sentences*, instead it will interact with the meaning only, and later have someone generate the corresponding *symbol* or sentence.

This can be thought of as having the pure meaning of something, which is then by some set of rule converted into *symbols* that can represent it. In natural language, this would be something like a translator, who analyzes sentences in one language to obtain the meaning, allowing him to translate it to any other language he knows. 

The example shows that once you have the pure meaning, you can essentially transform it into *symbols* using any rule set you like, and knowing the *rule set* that generated the *symbols*, you are able to infer the meaning once again.

Such a *rule-set* in terms of more natural language would be comparable to *grammar* which defines in which order *words* from a *vocabulary* may be put.

## The Semantics Framework

An implementation of semantic name handling is done in the *semantic framework* in *bsemantic*. It provides three major components:

- (*Semantic*)Nodes
 
    + They represent the meaning and carry pure, un-encoded information
    + Can be transformed into a single *symbol* in the sense of a *symbolic name*, which is compised of a sequence of characters.
    + Is called @ref bsemantic.base.ElementNode "ElementNode" in code
  
- (*Semantic*)Node Lists
 
    + They are similar to *sentences comprised of symbolic names*.
    + Can be transformed into a string with multiple symbols.
    + Is called @ref bsemantic.base.ElementNodeList "ElementNodeList" in code.
  
- *Rule Sets*
 
    + They can be compared with a *grammar* that marries meaning to a *vocabulary* of words, and defines possible relations of symbols.
    + Is called @ref bsemantic.base.ElementNodeTree ElementNodeTree in code
  
This framework can be used to transform meaning into symbols, or the inverse operation of extracting meaning from symbols.

### Encoding of Meaning

Lets visualize this first using a more natural terminology:

- The process of encoding meaning into a symbol or sentence first require you to have information that you would like to encode. The next step is to search the *grammar* for all *sentences* which are able to losslessly encode it. Finally, the information is placed into the symbols, which creates the final encoded sentence.
The same aspect using the technical terms could be phrased as follows:

- The information you would like to encode is contained in nested key-value dictionaries. Now you iterate the @ref bsemantic.base.ElementNodeTree "ElementNodeTree" to yield all @ref bsemantic.base.ElementNodeList "ElementNodeList" instances which are able to fully embody the information you provided. Each @ref bsemantic.base.ElementNode "ElementNode" in an @ref bsemantic.base.ElementNodeList "ElementNodeList" contains meaning implied by the data it may carry. You may further filter out those @ref bsemantic.base.ElementNodeList "ElementNodeLists"whose @ref bsemantic.base.ElementNode "ElementNodes" don't match your criteria. Finally you configure each @ref bsemantic.base.ElementNode "ElementNode" with the data you want it to represent, and transform it into a symbol string. This makes it some sort of *template* for the meaning you want it to carry.


### Decoding of Meaning

In natural terms, obtaining meaning from an encoded sentence would read as follows:

- Provided that you know the *grammar* and *vocabulary* used to create the *sentence*, you try to find the valid combination of symbols within your grammar and lookup the words used by the symbols in your vocabulary.

In technical terms, it reads a bit differently:

- Provided that you know the @ref bsemantic.base.ElementNodeTree "ElementNodeTree" used to create the *sentence*, iterate all @ref bsemantic.base.ElementNodeList "ElementNodeLists in the the tree and try to infer the configuration of each @ref bsemantic.base.ElementNode "ElementNode from left to right, and consume portions of the *sentence* from left to right. @ref bsemantic.base.ElementNodeList "ElementNodeLists" that could consume the whole *sentence* will be returned.

### Usage Tips
    
- Generally it is possible that a certain meaning is satisfied by multiple *sentences*, and that one *sentence* has multiple meanings, all depending on the *grammar*. This implies that there may always be multiple @ref bsemantic.base.ElementNodeList "ElementNodeLists" to handle, no matter if you are encoding or decoding *sentences*.
- If the code using this system does not assume a fixed grammar, it cannot assume any specific configuration of @ref bsemantic.base.ElementNode "ElementNodes" in the obtained @ref bsemantic.base.ElementNodeList "ElementNodeLists". All it may and must know about are the properties of the @ref bsemantic.base.ElementNode "ElementNodes" to determine where to apply which part of information.
- Each *grammar* needs proper testing to verify the code that interacts with it - its not a system that will just work magically, and code that uses it may still be buggy in one way or another.

