
## Semantic

A framework to translate meaning into symbols, and infer meaning from symbols, using a customizable ruleset.

### Preamble

"What's in a name ?" - one could say, and answer everything and nothing. A name itself is just a *sequence of characters*, and what makes it useful is the meaning we assign to those as a whole. If you take many of those sequences, lets call them *symbol* from now on, and place them in a specific order, they gain context which further defines their meaning - its a *sentence*.

For pipeline tool development, names used to playing a major roles, as they contain a lot of information and meaning that can be used to perform tasks. Meaning may be transformed as well, which generates a new name.

If code interacts with names, it usually has to either build those *symbols* that it believes belong to a meaning that it wants to express, or it tries to analyze the its characters to figure out its meaning, or the *symbols* in sentences to find out even more.

Doing so will of course make it very dependent on the actual character values, or the context of multiple concatenated *symbols*. This tends to be very problematic as they are prone to change, and sometimes they are required to change to adapt to changed requirements. 

In the end, what code is interested in is not the *symbol* itself, but the meaning that it bears, and we seek a way to decouple those so that the symbol can change, as long as the meaning doesn't.

### Semantic Name Handling

The solution to the inherent inflexibility of using *symbols* directly is to not actually do it. The only thing we want to and can keep static is the semantic aspect of a symbol, i.e. the meaning.

Code will not directly interact with names as strings, or with *symbols* in *sentences*, instead it will interact with the meaning only, and later have someone generate the corresponding *symbol* or sentence.

This can be thought of as having the pure meaning of something, which is then by some set of rule converted into *symbols* that can represent it. In natural language, this would be something like a translator, who analyzes sentences in one language to obtain the meaning, allowing him to translate it to any other language he knows. 

The example shows that once you have the pure meaning, you can essentially transform it into *symbols* using any rule set you like, and knowing the *rule set* that generated the *symbols*, you are able to infer the meaning once again.

Such a *rule-set* in terms of more natural language would be comparable to *grammar* which defines in which order *words* from a *vocabulary* may be put.

**Please see the documentation of the bsemantic package for more details**.
