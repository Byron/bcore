![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

TODO: WHY: dissolve the underlying folder structure and files, into a big tree of data. Deal with schema only, not with files or where data is coming from.

The configuration system allows to be comprised of multiple files located in a hierarchical directory tree. Configuration levels further down the tree will overwrite settings specified further up. This way, we may flexibly configure all aspects of the pipeline.

Additionally, configuration files can be conditional using a tag system, which allows to provide custom configuration based on the platform for instance, or the project's name.

The most convenient way to use the configuration is by far if you specify your schema in advance. This allows you to access your data safely, knowing that you will obtain value or your schema's default.

The schemas can also be used to verify the current configuration matches the requirements.

Configuration is stored in YAML format, which allows it to be nested.

The upcoming sections will explain the key features in further detail.

Configuration Hierarchy
=======================

All configuration files can be ordered in a hierarchy, which could look like this::
    
    ├── home
    │   └── user
    │       └── .pipeconfig
    │           └── userconfig.yaml
    └── projects
        ├── etc
        │   ├── host.maya.yaml
        │   ├── platform.lnx.yaml
        │   ├── platform.win.yaml
        │   ├── site.lnx.yaml
        │   ├── site.win.yaml
        │   └── site.yaml
        └── project
            ├── etc
            │   ├── host.maya.project.yaml
            │   └── site.project.yaml
            └── seq
                └── sq01
                    ├── etc
                    │   └── host.maya.yaml
                    └── shot01
                        └── etc
                            └── platform.lnx.yaml


The environment which sets up the configuration will do so based on its context, which may involve information about the project and shot used. From that, it can check for the existence of directories which are supposed to contain configuration files.

Those will be found top-down, having the most basic ones first, and more specific ones later. Those will override settings they have inherited so far by their parent configuration.

The user's home directory is used for its very own version of the configuration, which may finally override all other values. This is used to store custom settings.

A typical ordered set of configuration files for `shot1` could look like this::
    
    ./projects/etc/platform.lnx.yaml
    ./projects/etc/site.lnx.yaml
    ./projects/etc/host.maya.yaml
    ./projects/etc/site.yaml
    ./projects/project/etc/site.project.yaml
    ./projects/project/etc/host.maya.project.yaml
    ./projects/project/seq/sq01/etc/host.maya.yaml
    ./projects/project/seq/sq01/shot01/etc/platform.lnx.yaml
    
    ./home/user/.pipeconfig/userconfig.yaml

The user configuration is the only one that will receive actually changed values.

Tagged Configuration Files
==========================

Configuration files can be tagged to load them only if they match a given set of tags. This allows to conditionally load parts of the configuration, depending on some context.

Tags are separated by periods between the prefix and suffix of the file (**prefix.tag1[.tagN...].suffix**), such as in the following example::
    
    config.1.2.yaml
    config.win.32.yaml
    
The first file contains tags `1` and `2`, whereas the second contains `win` and `32`. They will be contained in the list of configuration files to use only if all of their tags match the ones specified by the one setting up the configuration.

Nested Configuration Options
============================

As configuration files are stored in `yaml markup format <http://www.yaml.org/>`_, you can easily represent complex nested values. This helps you to keep you configuration file very extensible, yet easy to read. No longer are you confined to the constraints of the INI file format, or have to deal with hard-to-read XML files.

An example yaml configuration file could look as follows - note the structure having more than 2 levels::

```yaml    
# site.yaml
# site configuration which will always be loaded
site:                   # Site specific configuration
  name: klenze7
  location: munich
  
db:                     # all database specific configuration 
  meta:                 # meta database with all kinds of info
    server_url: metadb.domain.intern
  ldap:                 # ldap service for additional user information
    server_url: ldp://ldap.domain.intern
```
        
    
Designing Configuration Files
=============================

As the system will always work with multiple configuration files, its possible and recommended to split up the configuration into related parts, where each part resides in an own configuration file.

In conjunction with configuration file `tagging`, you can split up configuration to be even more specific.

Software using the configuration can be completely platform or context agnostic.

Your configuration is has to be designed on two levels: first you need to know how to organize the information, and thus its taxonomy. This allows you to setup a tree of values which represents the information.

This tree can then be split up into segments and distributed in multiple files, which once again allows configuration to be loaded conditionally.


Configuration Tree
------------------

Its worth thinking about this tree in advance, as it is vital to keep your configuration organized. This helps you to easily find what you are looking for, and prevents accidental duplication of options.

First it would be good to know what kind of information to keep, and place it into nested categories. When navigating the categories, the options which follow as leafs should fit naturally.

A simple example could be site information, which could look as follows::

```yaml    
# Specifies the trixte munich site
site:
  name: klenze7
  location: 
    name: munich
    coord:                      # geographical coordinates
      longitude: 48.136607
      latitude: 11.577085
```
          
Urls into this tree would be `site.name` for instance, or `site.location.coord.longitude`. If it feels natural and leaves space for future extension, your tree is on a good way already.
        

Configuration File Names
------------------------

A possible file naming scheme could easily be dependent on the top-level options in your configuration.
    
* **platform**.<name>.yaml
    * Contains information about the respective platform, in case it cannot be determined automatically using facilities within the programming language. It is using a tag with the `name` of the platform to load it only conditionally.
 
* **site**.yaml
    * Contains all information about the site, like its name and location.
 
* **host**.yaml
    * Information about the host-software that is currently running the python interpreter.

Any other scheme will do as well, sometimes it can even be more convenient to store everything in one file.

Using the API
=============

If you like to use the configuration system using an API, please consult the pipeline API docs.

.. todo:: try to link to the api docs.
