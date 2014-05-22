The bcore project is designed to help writing powerful and maintainable application rapidly.

## Features

These are the top-three features

- bootstrapper for dependency handling and pre-runtime configuration of programs
- service registry for plugins and configuration
- file based, cascading key-value store with schema support

Among the additional features are

- Path type for object oriented path handling
- small utility types too numerous to mention
- a simple framework for writing and running quality checks
- a simple framework to write transaction based operations of any kind
- a framework for building powerful commandline tools
- [a framework](https://github.com/Byron/bcore/blob/master/src/md/bsemantic.md) for generating names in a rule based fashion, and infering meaning from them

## Requirements

The requirements are kept minimal, which is why you need nothing more than:

* a python 2.6 or 2.7 interpreter running on Linux, OSX, Solaris or Windows

Optionally, you may need the following

* nosetests
    -  Developers use it to run unit tests to verify the program works as expected

## Development Status

[![Coverage Status](https://coveralls.io/repos/Byron/bcore/badge.png)](https://coveralls.io/r/Byron/bcore)
[![Build Status](https://travis-ci.org/Byron/bcore.svg?branch=master)](https://travis-ci.org/Byron/bcore)

The code base was initiated 1.5 years ago, and was created to faciliate development in the company I was working for. Thanks to a code-buyback deal I am able to open-source it.

Currently I am fixing long-standing issues and clean up the entire code-base. This makes the code highly-instable, in the sense of it changing a lot and at will.

Once the first release is out of the door, the API will stabilize though, yet I don't feel like being too careful about it as long as there are no strong dependencies on the code.

![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

## Credits / External Packages

* [yaml](http://yaml.org)
* [parse](https://github.com/r1chardj0n3s/parse)

### LICENSE

This open source software is licensed under [GNU Lesser General Public License](https://github.com/Byron/bcore/blob/master/LICENSE.md)
