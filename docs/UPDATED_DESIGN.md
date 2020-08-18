# TODO :
- proper sphinx doc with maximum in code...


# DESIGN

The main concepts available at teh root of the package currently need initialization, so we asynchronousl do a first REST request to retrieve data.
Note in the future, we aim to keep data locally, so this will not be needed (except maybe the first time), as the pacakge will reuse the stored data.

We combine both REST and WSS behavior in this way :
- REST is request-response paradigm. This is handled via the `__call__` method.
- WSS is a subscribe-receiver paradigm. This is handled via the `__aiter__` method.
- since `__aiter__` behaviro is to look forward in time into the unknown, `__iter__` also look forward in time, but stops when it reaches 'now'.

 
Depending on their nature the various API concepts are mappings with keys in:
- pairs
- assets
- time

Internally pandas Dataframe provide the functionality we need to manipulate time indexed data.

As a debug feature, a bokeh server could be provided...
