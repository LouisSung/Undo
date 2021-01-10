import gc
import sys
from typing import Callable, List, Tuple


class UndoFunc:
    def __init__(self):
        self.hihi = []
        self._undo_stack: List[Tuple[Callable, Callable]] = []

    def say_hi_to(self, name: str) -> Tuple[Callable, List[str]]:
        _local_undo_stack: List[Callable] = []

        # === Start Doing Stuff ===
        stuff_result: List[str] = []
        self.hihi.append(stuff_result)
        # Use `remove()` instead of `pop()` to support unordered undo
        _local_undo_stack.append(lambda: self.hihi.remove(stuff_result))

        stuff_result.append('Hi')
        # The `pop()` does not support unordered undo but it's OK for (linear) local undo
        _local_undo_stack.append(lambda: stuff_result.pop())
        stuff_result.append(name)
        _local_undo_stack.append(lambda: stuff_result.pop())
        # === End Doing Stuff ===

        return self._undo_func_call(_local_undo_stack, lambda: self.hihi.remove(stuff_result)), stuff_result

    def undo(self, undo_all: bool = False, purge: bool = False) -> int:
        if len(self._undo_stack) == 0:
            return -1
        elif purge:
            while self._undo_stack:
                (self._undo_stack.pop()[1])()
        else:
            # Undo funcs in the reverse order
            # Don't do the `pop()` here, it's done in the end of the inner `_undo_a_func()`
            while self._undo_stack:
                (self._undo_stack[-1][0])()
                if not undo_all:  # undo once only
                    break
        return len(self._undo_stack)

    def _undo_func_call(self, local_undo_stack: List[Callable], purge_callback: Callable = lambda: None) -> Callable:
        def _undo_a_func():
            if hasattr(_undo_a_func, 'has_called'):
                raise ValueError('NEVER invoke the returned `undo()` twice')
            else:
                _undo_a_func.__setattr__('has_called', True)
                while local_undo_stack:
                    (local_undo_stack.pop())()
                # Remove self (i.e., lambda: _undo_a_func()) from the global undo stack
                self._undo_stack.remove(_undo_a_func._undo_lambdas)

        _undo_a_func._undo_lambdas = (lambda: _undo_a_func(), lambda: purge_callback())
        self._undo_stack.append(_undo_a_func._undo_lambdas)
        return _undo_a_func._undo_lambdas[0]


if __name__ == '__main__':
    demo = UndoFunc()
    _, result = demo.say_hi_to('World')  # use _ to consume useless undo
    print(result)  # ['Hi', 'World']
    undo, result = demo.say_hi_to('Gura')
    print(demo.hihi, result)  # [['Hi', 'World'], ['Hi', 'Gura']] ['Hi', 'Gura']

    undo()
    # undo()  # !!! [UNCOMMENT] ValueError: NEVER invoke the returned `undo()` twice
    print(demo.hihi)  # [['Hi', 'World']]

    demo.undo()
    print(demo.hihi)  # []

    result = demo.say_hi_to('A')[1]
    print(result)  # ['Hi', 'A']
    demo.say_hi_to('SHAAAAAARK')
    print(demo.hihi)  # [['Hi', 'A'], ['Hi', 'SHAAAAAARK']]
    demo.say_hi_to('MEATLOAF')
    print(demo.hihi)  # [['Hi', 'A'], ['Hi', 'SHAAAAAARK'], ['Hi', 'MEATLOAF']]

    print(demo.undo())  # undo the last one (3 -> 2), returned 2
    print(demo.undo(undo_all=True))  # undo all (2 -> 0), returned 0
    print(demo.hihi)  # []
    print(demo.undo())  # nothing to undo (0 -> 0), returned -1

    # Unordered Undo (requires the function local undo also be well designed)
    undo1, _ = demo.say_hi_to('1. unordered')
    undo2, _ = demo.say_hi_to('2. undo')

    undo1()  # undo1 (second last) instead of undo2 (last)
    print(demo.hihi)  # [['Hi', '2. undo']]
    undo2()
    print(demo.hihi)  # []

    # FIXME: Uncomment following code to check if garbage collection gets invoked
    # memcheck_func = UndoFunc()
    # memcheck_purge = UndoFunc()
    # while True:
    #     memcheck_instance = UndoFunc()
    #
    #     for i in range(620):
    #         memcheck_instance.say_hi_to('Bloop')  # auto garbage collected
    #
    #         memcheck_func.say_hi_to('Trident')
    #         # memcheck_func.undo()  # [UNCOMMENT] prevent the ref_func & gc_count from growing
    #
    #         undo, _ = memcheck_func.say_hi_to('Floaties')
    #         # undo()  # [UNCOMMENT] prevent the ref_func & gc_count from growing
    #
    #         memcheck_purge.say_hi_to('padowo')
    #         # memcheck_purge.undo(purge=True)  # [UNCOMMENT] prevent the ref_purge & gc_count from growing
    #
    #     ref_func, ref_instance = sys.getrefcount(memcheck_func), sys.getrefcount(memcheck_instance)
    #     ref_purge, gc_count = sys.getrefcount(memcheck_purge), len(gc.get_objects())
    #     print(f'[RefCount]Instance: {ref_instance}, Func: {ref_func: >3}, Purge: {ref_purge: >2}; GC: {gc_count: >6}')
