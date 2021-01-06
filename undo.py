from typing import Callable, List, Tuple


class UndoDemo:
    def __init__(self):
        self.hihi = []
        self._undo_stack: List[Callable] = []

    def say_hi_to(self, name: str) -> Tuple[Callable, Tuple[str, ...]]:
        _local_undo_stack: List[Callable] = []

        # === start doing stuff ===
        tmp_list: List[str] = []
        self.hihi.append(tmp_list)
        # use `remove()` instead of `pop()` to support unordered undo
        _local_undo_stack.append(lambda: self.hihi.remove(tmp_list))

        tmp_list.append('Hi')
        # `pop()` does not support unordered undo but it's ok for local undo
        _local_undo_stack.append(lambda: tmp_list.pop())
        tmp_list.append(name)
        _local_undo_stack.append(lambda: tmp_list.pop())

        _result = tuple(tmp_list)
        # === end doing stuff ===

        return self._undo_a_func(_local_undo_stack), _result

    def undo(self, undo_all: bool = False) -> bool:
        if len(self._undo_stack) == 0:
            return False  # nothing to undo
        else:
            # undo funcs in reverse order
            # don't do `pop()` here, it's done in the end of the inner `undo_a_func()`
            while self._undo_stack:
                (self._undo_stack[-1])()
                if not undo_all:
                    break  # undo once only
            return True

    def _undo_a_func(self, func_local_undo_stack: List[Callable]) -> Callable:
        def undo_func():
            if hasattr(undo_func, 'has_called'):
                raise ValueError('NEVER invoke the returned `undo()` twice')
            else:
                undo_func.__dict__['has_called'] = True
                while func_local_undo_stack:
                    (func_local_undo_stack.pop())()
                # remove self (i.e., lambda: undo_func()) from the global undo stack
                self._undo_stack.remove(undo_func.__dict__['undo_lambda'])

        undo_func.undo_lambda = lambda: undo_func()
        self._undo_stack.append(undo_func.undo_lambda)
        return undo_func.undo_lambda


if __name__ == '__main__':
    demo = UndoDemo()
    _, result = demo.say_hi_to('World')  # use _ to consume useless undo
    print(result)  # ('Hi', 'World')
    undo, result = demo.say_hi_to('Gura')
    print(demo.hihi, result)  # [['Hi', 'World'], ['Hi', 'Gura']] ('Hi', 'Gura')

    undo()
    # undo()  # !!! ValueError: NEVER invoke the returned `undo()` twice
    print(demo.hihi)  # [['Hi', 'World']]

    demo.undo()
    print(demo.hihi)  # []

    result = demo.say_hi_to('A')[1]
    print(result)  # ('Hi', 'A')
    demo.say_hi_to('SHAAAAAARK')
    print(demo.hihi)  # [['Hi', 'A'], ['Hi', 'SHAAAAAARK']]

    demo.undo(undo_all=True)
    print(demo.hihi)  # []
    demo.undo()  # nothing will happen (i.e., nothing to undo, return False)

    # Unordered Undo (requires the function local undo also be well designed)
    undo1, _ = demo.say_hi_to('1. unordered')
    undo2, _ = demo.say_hi_to('2. undo')

    undo1()  # undo1 (second last) instead of undo2 (last)
    print(demo.hihi)  # [['Hi', '2. undo']]
    undo2()
    print(demo.hihi)  # []
