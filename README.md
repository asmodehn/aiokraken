# aiokraken
[![Build Status](https://travis-ci.org/asmodehn/aiokraken.svg?branch=develop)](https://travis-ci.org/asmodehn/aiokraken)
[![Updates](https://pyup.io/repos/github/asmodehn/aiokraken/shield.svg)](https://pyup.io/repos/github/asmodehn/aiokraken/)
[![Python 3](https://pyup.io/repos/github/asmodehn/aiokraken/python-3-shield.svg)](https://pyup.io/repos/github/asmodehn/aiokraken/)

Python asyncio client for Kraken REST and Websockets API

We follow the [gitflow](https://danielkummer.github.io/git-flow-cheatsheet/) workflow for branches:
  - Developer should base their work on `develop`.
  - Users should use the version from `master` (also released as a PyPI package)

## Installation 
    pip install aiokraken

## Running packaged tests
    python -m aiokraken.model.tests
    
## Running integration tests (developer)
    pytest tests/aiokraken/rest   # for replay using cassettes
    pytest tests/aiokraken/rest --with-keyfile --record-mode=all  # for actual server integration test

## [REST example](https://github.com/dantimofte/aiokraken/blob/master/aiokraken/examples/rest_example.py)

    from aiokraken import RestClient
    async def get_assets():
        """ get kraken time"""
        rest_kraken = RestClient()

        response = await rest_kraken.assets()
        print(f'response is {response}')

        await rest_kraken.close()
    
    asyncio.get_event_loop().run_until_complete(get_assets())

## [websocket example](https://github.com/dantimofte/aiokraken/blob/master/aiokraken/examples/wss_example.py)

## Running the bokeh app
     bokeh serve --show aiokraken/bokeh_app/ohlc_dynfig.py 


## Documentation

## Compatibility

- python 3.7 and above

## Contributing

Contributions are welcome and PR will be merged into develop as quickly as possible.

Here are some guidelines that makes everything easier for everybody:

1. Fork it.
2. Create a feature branch containing only your fix or feature.
3. Add/Update tests.
4. Create a pull request.

### TODO

- Write documentation for the library

## References

https://www.kraken.com/features/api

## Licence

The MIT License (MIT)

TODO : Change to GPL (NB: Dan is okay)
