#-*-coding:utf-8-*-
"""
@package tx.template
@brief A package containing a flexible templating engine used to generate paths.

@page templates Template Framework

The Template Framework
======================

An implementation of semantic name handling is done in the *template framework* in *tx.template*. 
It provides three major components:

- (*Semantic*)Nodes
 
 + They represent the meaning and carry pure, un-encoded information
 + Can be transformed into a single *symbol* in the sense of a *symbolic name*, which is compised of a 
   sequence of characters.
 + Is called @ref tx.template.base.ElementNode "ElementNode" in code
  
- (*Semantic*)Node Lists
 
 + They are similar to *sentences comprised of symbolic names*.
 + Can be transformed into a string with multiple symbols.
 + Is called @ref tx.template.base.ElementNodeList "ElementNodeList" in code.
  
- *Rule Sets*
 
 + They can be compared with a *grammar* that marries meaning to a *vocabulary* of words, and defines 
   possible relations of symbols.
 + Is called @ref tx.template.base.ElementNodeTree ElementNodeTree in code
  
This framework can be used to transform meaning into symbols, or the inverse operation of extracting meaning 
from symbols.

Encoding of Meaning
===================
Lets visualize this first using a more natural terminology:

- The process of encoding meaning into a symbol or sentence first require you to have information that you 
  would like to encode.

  The next step is to search the *grammar* for all *sentences* which are able to losslessly encode it.

  Finally, the information is placed into the symbols, which creates the final encoded sentence.

The same aspect using the technical terms could be phrased as follows:

- The information you would like to encode is contained in nested key-value dictionaries.
    
  Now you iterate the @ref tx.template.base.ElementNodeTree "ElementNodeTree" to yield all 
  @ref tx.template.base.ElementNodeList "ElementNodeList" instances which are able to fully embody 
  the information you provided. Each @ref tx.template.base.ElementNode "ElementNode" in an 
  @ref tx.template.base.ElementNodeList "ElementNodeList" contains meaning implied by the data 
  it may carry. You may further filter out those @ref tx.template.base.ElementNodeList "ElementNodeLists" 
  whose @ref tx.template.base.ElementNode "ElementNodes" don't match your criteria. 
    
  Finally you configure each @ref tx.template.base.ElementNode "ElementNode" with the data you want 
  it to represent, and transform it into a symbol string. This makes it some sort of *template* for the 
  meaning you want it to carry.


Decoding of Meaning
===================

In natural terms, obtaining meaning from an encoded sentence would read as follows:

- Provided that you know the *grammar* and *vocabulary* used to create the *sentence*, you try to find the 
  valid combination of symbols within your grammar and lookup the words used by the symbols in your vocabulary.
    
In technical terms, it reads a bit differently:

- Provided that you know the @ref tx.template.base.ElementNodeTree "ElementNodeTree" used to create 
  the *sentence*, iterate all @ref tx.template.base.ElementNodeList "ElementNodeLists in the the tree 
  and try to infer the configuration of each @ref tx.template.base.ElementNode "ElementNode from left 
  to right, and consume portions of the *sentence* from left to right. 
  @ref tx.template.base.ElementNodeList "ElementNodeLists" that could consume the whole *sentence* 
  will be returned.


Usage Tips
===========
    
- Generally it is possible that a certain meaning is satisfied by multiple *sentences*, and that one *sentence* 
  has multiple meanings, all depending on the *grammar*. This implies that there may always be multiple 
  @ref tx.template.base.ElementNodeList "ElementNodeLists" to handle, no matter if you are encoding or 
  decoding *sentences*.
- If the code using this system does not assume a fixed grammar, it cannot assume any specific configuration 
  of @ref tx.template.base.ElementNode "ElementNodes" in the obtained 
  @ref tx.template.base.ElementNodeList "ElementNodeLists". All it may and must know about are the 
  properties of the @ref tx.template.base.ElementNode "ElementNodes" to determine where to apply which 
  part of information.
- Each *grammar* needs proper testing to verify the code that interacts with it - its not a system that will 
  just work magically, and code that uses it may still be buggy in one way or another.


@copyright 2012 Sebastian Thiel
"""

from .base import *
from .exceptions import *
from .generators import *
from .inference import *
