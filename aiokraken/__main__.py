# TODO : strict minimal ipython REPL launcher to use aiokraken.
# Nice TUI|GUI can be done in another project.

# !/usr/bin/env python
# Ref : https://ipython.org/ipython-doc/stable/interactive/reference.html#embedding-ipython


"""
__main__ has only the code required to start IPython and provide interactive introspection of aiokraken while running
"""

import click

from aiokraken import RestClient
from aiokraken.assets import Assets
from aiokraken.rest import Server

# TODO : we should probably have a ipython terminal option (ipywidgets without notebook ?)
#      Bokeh is also a solution for a server to provide visualization,
#      AND an aiohttp server option to provide json feeds (like original server, visualized with some js single page app...)


def ipshell_embed_setup():

    from traitlets.config.loader import Config

    try:
        get_ipython
    except NameError:
        nested = 0
        cfg = Config()
    else:
        print("Running nested copies of IPython.")
        print("The prompts for the nested copy have been modified")
        cfg = Config()
        nested = 1

    # First import the embeddable shell class
    from IPython.terminal.embed import InteractiveShellEmbed

    # Now create an instance of the embeddable shell. The first argument is a
    # string with options exactly as you would type them if you were starting
    # IPython at the system command line. Any parameters you want to define for
    # configuration can thus be specified here.
    ipshell = InteractiveShellEmbed(config=cfg,
                                    banner1='Dropping into IPython',
                                    banner2='To introspect: %whos',
                                    exit_msg='Leaving Interpreter, back to program.')

    # Remember the dummy mode to disable all embedded shell calls!

    return ipshell



@click.group()
def cli():
    pass


@cli.command()
@click.option('--verbose', default=False)
@click.pass_context
def auth(ctx, verbose):
    """ simple command to verify auth credentials and optionally store them. """
    from aiokraken.config import KRAKEN_API_KEYFILE, load_api_keyfile, save_api_keyfile
    # tentative loading of the API key
    keystruct = load_api_keyfile()

    if keystruct is None:
        # no keyfile found
        print(f"{KRAKEN_API_KEYFILE} not found !")
        # TODO : check for interactive terminal...
        apikey = input("APIkey: ")
        secret = input("secret: ")
        store = input(f"Store it in {KRAKEN_API_KEYFILE} [Y/n] ? ")
        if not store:
            store = 'Y'
        if store in ['Y', 'y']:
            keystruct = save_api_keyfile(apikey=apikey, secret=secret)
        else:
            keystruct = {'key': apikey, 'secret': secret}

    # modifying parent context if present (to return)
    if ctx.parent:
        ctx.parent.params['apikey'] = keystruct.get('key')
        ctx.parent.params['secret'] = keystruct.get('secret')
    if verbose:
        print(f"apikey: {ctx.apikey}")
        print(f"secret: {ctx.secret}")

    return 0  # exit status code


def one_shot(coro):
    import asyncio
    loop = asyncio.get_event_loop()

    loop.run_until_complete(coro)

    loop.close()


async def assets_run():

    rest = RestClient(server=Server())

    assets = Assets(blacklist=[])
    res = await assets(rest_client=rest)
    for k, p in res.items():
        print(f" - {k}: {p}")


@cli.command()
@click.pass_context
def assets(ctx):
    """ retrieve assets """

    return one_shot(assets_run())


# For OHLC timeseries display : https://stackoverflow.com/questions/48361554/unknown-error-in-mpl-finance-candlestick-what-to-do

async def markets_run():

    rest = RestClient(server=Server())

    mkts = Markets()
    await mkts()
    for k, p in mkts.items():
        print(f" - {k}: {p}")


@cli.command()
@click.pass_context
def markets(ctx):
    """ retrieve markets"""
    return one_shot(markets_run())


async def balance_run(key,secret):
    rest = RestClient(server=Server(key=key,
                                    secret=secret))
    balance = Balance(blacklist=[])
    await balance(rest_client=rest)
    for k, p in balance.items():
        print(f" - {k}: {p}")


@cli.command()
@click.option('--apikey', default=None)
@click.option('--secret', default=None)
@click.pass_context
def balance(ctx, apikey, secret):
    """ retrieve balance for an authentified user"""

    if apikey is None or secret is None:
        ctx.invoke(auth, verbose=False)  # this should fill up arguments
        apikey = ctx.params.get('apikey')
        secret = ctx.params.get('secret')

    # ipshell = ipshell_embed_setup()
    # ipshell(f"from {__name__}")

    # TODO : some meaningful and useful link between markets and assets ?
    return one_shot(balance_run(key=apikey, secret=secret))


# TODO : retrieve private data
# TODO : allow passing orders


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # we use click to run a simple command
        cli()
    else:
        # or we go full interactive mode (no args)

        # First create a config object from the traitlets library
        from traitlets.config import Config
        c = Config()

        # Now we can set options as we would in a config file:
        #   c.Class.config_value = value
        # For example, we can set the exec_lines option of the InteractiveShellApp
        # class to run some code when the IPython REPL starts
        c.InteractiveShellApp.exec_lines = [
            'print("\\nimporting aiokraken...\\n")',
            'import aiokraken',
            "aiokraken"
        ]
        c.InteractiveShell.colors = 'LightBG'
        c.InteractiveShell.confirm_exit = False
        c.TerminalIPythonApp.display_banner = False

        #TODO : %autoawait to easily run requests

        # Now we start ipython with our configuration
        import IPython
        IPython.start_ipython(config=c, )




