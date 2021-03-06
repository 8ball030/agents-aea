Release History
===============

0.1.0 (2019-08-21)
-------------------

- Initial release of the package.

0.1.1 (2019-09-04)
-------------------

- Provides examples and fixes.

0.1.2 (2019-09-16)
-------------------

- Adds aea cli tool.
- Adds aea skills framework.
- Introduces static typing checks across aea, using Mypy.
- Extends gym example

0.1.3 (2019-09-19)
-------------------

- Adds Jenkins for CI
- Adds docker develop image
- Parses dependencies of connections/protocols/skills on the fly
- Adds validations of config files
- Adds first two working skills and fixes gym examples
- Adds docs
- Multiple additional minor fixes and changes

0.1.4 (2019-09-20)
-------------------

- Adds cli functionality to add connections
- Multiple additional minor fixes and changes

0.1.5 (2019-09-26)
-------------------

- Adds scaffolding command to the CLI tool
- Extended docs
- Increased test coverage
- Multiple additional minor fixes and changes

0.1.6 (2019-10-04)
-------------------

- Adds several new skills
- Extended docs on framework and skills
- Introduces core framework components like decision maker and shared classes
- Multiple additional minor fixes and changes

0.1.7 (2019-10-14)
-------------------

- Adds gui to interact with cli
- Adds new connection stub to read from/write to file
- Adds ledger entities (fetchai and ethereum); creates wallet for ledger entities
- Adds more documentation and fixes old one
- Multiple additional minor fixes and changes

0.1.8 (2019-10-18)
-------------------

- Multiple bug fixes and improvements to gui of cli
- Adds full test coverage on cli
- Improves docs
- Multiple additional minor fixes and changes

0.1.9 (2019-10-18)
-------------------

- Stability improvements
- Higher test coverage, including on Python 3.6
- Multiple additional minor fixes and changes

0.1.10 (2019-10-19)
-------------------

- Compatibility fixes for Ubuntu and Windows platforms
- Multiple additional minor fixes and changes

0.1.11 (2019-10-30)
-------------------

- Adds python3.8 test coverage
- Adds almost complete test coverage on aea package
- Adds filter concept for message routing
- Adds ledger integrations for fetch.ai and ethereum
- Adds carpark examples and ledger examples
- Multiple additional minor fixes and changes

0.1.12 (2019-11-01)
-------------------

- Adds TCP connection (server and client)
- Fixes some examples and docs
- Refactors crypto modules and adds additional tests
- Multiple additional minor fixes and changes

0.1.13 (2019-11-08)
-------------------

- Adds envelope serializer
- Adds support for programmatically initializing an AEA
- Adds some tests for the gui and other components
- Exposes connection status to skills
- Updates oef connection to re-establish dropped connections
- Updates the car park agent
- Multiple additional minor fixes and changes

0.1.14 (2019-11-29)
-------------------

- Removes dependency on OEF SDK's FIPA API
- Replaces dialogue id with dialogue references
- Improves CLI logging and list/search command output
- Introduces multiplexer and removes mailbox
- Adds much improved tac skills
- Adds support for CLI integration with registry
- Increases test coverage to 99%
- Introduces integration tests for skills and examples
- Adds support to run multiple connections from CLI
- Updates the docs and adds uml diagrams
- Multiple additional minor fixes and changes
