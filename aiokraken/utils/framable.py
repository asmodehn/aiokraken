# TODO : protocol (see PEP 544) from python 3.8
import inspect

import wrapt
import static_frame as sf


def framable(*params):

    def decorator(pydef):

        if inspect.isclass(pydef):
            fields = pydef.__annotations__

            frame = sf.Frame.from_records(records=[], columns=[k for k in fields.keys()], dtypes=[v for v in fields.values()])

        elif callable(pydef):
            sig = inspect.signature(pydef)
            print(sig)

            params = sig.parameters
            result = sig.return_annotation

            frame = sf.Frame.from_records(records=[],
                                          columns=[k for k in params.keys()] + ["result"],)
                                          # dtypes=[v for v in params.values()] + [result])  # probably not needed (careful when return annotation is empty.

        else:
            raise NotImplementedError

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):

            sig = inspect.signature(wrapped)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            params = bound_args.arguments

            if instance is None:  # wrapped is a procedure or a class

                if inspect.isclass(pydef):
                    attrs = pydef.__annotations__
                else:
                    attrs = sig.parameters

                # TODO : in class case, we probably do not want to keep the instance IN the frame... (maybe in a map, indexed on tuple from frame ?)

                res = wrapped(*bound_args.args, **bound_args.kwargs)
                # Note : we assume matching parameters (from signature) and arguments (from bound_args).
                wrapped.frame = sf.Frame.from_records(records=[t for t in wrapped.frame.iter_tuple(1)] + [(*bound_args.arguments.values(), res)],
                                                      columns=[k for k in attrs.keys()] + ["result"],)
                                                      # dtypes=[v for v in params.values()] + [result])  # lets infer types from data, dynamically, python style.
                return res

            else:  # wrapped is a method !
                raise NotImplementedError

        wrapd = wrapper(pydef)
        wrapd.frame = frame
        return wrapd

    return decorator


if __name__ == '__main__':

    @framable()
    def myfun(arg: int):
        return 42

    print(myfun(51))

    print(myfun.frame)

    @framable()
    class mycls:
        field1: int

        def __init__(self, val):
            self.field1 = val


    inst = mycls(51)

    print(inst)
    print(inst.frame)














