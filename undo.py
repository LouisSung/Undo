import gc
import sys
from typing import Callable, List, Tuple


class UndoAble:
    def __init__(self):
        self._undo_stack: List[Tuple[Callable, Callable]] = []

    def undo(self, undo_last: int = 1, undo_all: bool = False) -> int:
        if len(self._undo_stack) == 0 or undo_last < 1:
            return -1  # nothing to undo
        undo_count = len(self._undo_stack) if undo_all else min(undo_last, len(self._undo_stack))
        for _ in range(undo_count):  # undo
            (self._undo_stack[-1][0])()  # use [-1] instead of pop() because it's done by the inner _remove_lambdas()
        return len(self._undo_stack)

    def purge_undo(self, purge_last: int = 1, purge_all: bool = True) -> int:
        if len(self._undo_stack) == 0 or purge_last < 1:
            return -1  # nothing to purge
        purge_count = len(self._undo_stack) if purge_all else min(purge_last, len(self._undo_stack))
        for _ in range(purge_count):  # purge
            (self._undo_stack.pop()[1])()
        return len(self._undo_stack)

    def merge_undo(self, merge_last: int = 2, merge_all: bool = True):
        merge_count = len(self._undo_stack) if merge_all else max(min(merge_last, len(self._undo_stack)), 0)
        merged_undo = reversed(self._undo_stack[-merge_count:])
        del self._undo_stack[-merge_count:]
        self._register_func_undo(
            [lambda: [undo_merged() for undo_merged, _ in merged_undo]],
            lambda: [purge_merged() for purge_merged, _ in merged_undo]
        )

    def _register_func_undo(self, local_undo_stack: List[Callable],
                            purge_callback: Callable = lambda: None) -> Callable:
        def _undo_func() -> int:
            if hasattr(_undo_func, 'has_called'):  # should never call an undo twice
                raise ValueError('NEVER invoke the returned `undo()` twice')
            else:
                _undo_func.__setattr__('has_called', True)
                while local_undo_stack:  # undo a function
                    (local_undo_stack.pop())()
                if _undo_func._undo_lambdas not in self._undo_stack:
                    return -1
                self._undo_stack.remove(_undo_func._undo_lambdas)
                return len(self._undo_stack)

        _undo_func._undo_lambdas = (lambda: _undo_func(), lambda: purge_callback())  # no memory leaks here
        self._undo_stack.append(_undo_func._undo_lambdas)
        return _undo_func._undo_lambdas[0]  # return undo handler


class UndoAbleFunc(UndoAble):
    def __init__(self):
        super().__init__()
        self.hihi: List[List[str]] = []

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

        return self._register_func_undo(_local_undo_stack), stuff_result


if __name__ == '__main__':
    demo = UndoAbleFunc()
    # === [Basic] Undo ===
    _, result = demo.say_hi_to('Gawr')  # use _ to consume useless undo
    print('result:', result)  # result: ['Hi', 'Gawr']
    undo, result = demo.say_hi_to('Gura')
    print('hihi01:', demo.hihi, '; result:',  result)  # hihi01: [[...], [...]] ; result: ['Hi', 'Gura']

    undo()
    # undo()  # !!! [UNCOMMENT] ValueError: NEVER invoke the returned `undo()` twice
    print('hihi02:', demo.hihi)  # hihi02: [['Hi', 'Gawr']]

    demo.undo()
    print('hihi03:', demo.hihi)  # hihi03: []

    result = demo.say_hi_to('A')[1]
    demo.say_hi_to('SHAAAAAARK')
    demo.say_hi_to('MEATLOAF')
    print('hihi04:', demo.hihi)  # hihi04: [['Hi', 'A'], ['Hi', 'SHAAAAAARK'], ['Hi', 'MEATLOAF']]

    print('stack01', demo.undo())  # stack01: 2, undo the last one (3) [A, S, M] -> (2) [A, S], returned 2
    print('hihi05:', demo.hihi)  # hihi05: [['Hi', 'A'], ['Hi', 'SHAAAAAARK']]
    print('stack02:', demo.undo(undo_all=True))  # stack02: 0, undo all (2) [A, S] -> (0) [], returned 0
    print('hihi06:', demo.hihi)  # hihi06: []
    print('stack03:', demo.undo())  # stack03: -1, nothing to undo (0) [] -> (0) [], returned -1

    # === [Basic] Purge Undo ===
    demo.say_hi_to('Gawr')
    undo, _ = demo.say_hi_to('Gura')
    print('stack04:', len(demo._undo_stack), '; hihi07:', demo.hihi)  # stack04: 2 ; hihi07: [[...], [...]]
    demo.purge_undo()
    print('stack05:', len(demo._undo_stack), '; hihi08:', demo.hihi)  # stack05: 0 ; hihi08: [[...], [...]]
    print('stack06:', undo())  # stack06: -1
    print('stack07:', demo.undo())  # stack07: -1
    demo.hihi.clear()

    # === [Basic] Merge Undo ===
    demo.say_hi_to('Gawr')
    demo.say_hi_to('Gura')
    undo, _ = demo.say_hi_to('Bloop')
    print('stack08:', len(demo._undo_stack), '; hihi09:', demo.hihi)  # stack08: 3 ; hihi09: [[...], [...], [...]]
    demo.merge_undo()  # merge all: (3) [Gawr, Gura, Bloop] -> (1) [[Gawr, Gura, Bloop]]
    print('stack09:', len(demo._undo_stack), '; hihi10:', demo.hihi)  # stack09: 1 ; hihi10: [[...], [...], [...]]
    # print('stackXX:', undo(), '; hihiXX:', demo.hihi)  # stackXX: 1 ; hihiXX: [[...], [...]]
    print('stack10:', demo.undo(), '; hihi11:', demo.hihi)  # stack10: 0 ; hihi11: []
    # undo()  # !!! [UNCOMMENT] ValueError: NEVER invoke the returned `undo()` twice

    demo.say_hi_to('Gawr')
    demo.say_hi_to('Gura')
    demo.say_hi_to('Bloop')
    demo.merge_undo(merge_all=False)  # merge last 2 by default
    print('stack11:', len(demo._undo_stack))  # stack11: 2
    print('stack12:', demo.undo(), '; hihi12:', demo.hihi)  # stack12: 1 ; hihi12: [['Hi', 'Gawr']]

    demo.say_hi_to('Gura')
    demo.say_hi_to('Bloop')
    demo.merge_undo(merge_all=False)  # merge last 2 once: (3) [Gawr, Gura, Bloop] -> (2) [Gawr, [Gura, Bloop]]
    demo.merge_undo(merge_all=False)  # merge last 2 twice: (2) [Gawr, [Gura, Bloop]] -> (1) [[Gura, [Gura, Bloop]]]
    print('stack13:', len(demo._undo_stack), '; hihi13:', demo.hihi)  # stack13: 1 ; hihi13: [[...], [...], [...]]
    print('stack14:', demo.undo(), '; hihi14:', demo.hihi)  # stack14: 0 ; hihi14: []

    # === [Advanced][WARNING] Unordered Undo Example (requires the function local undo also be well designed) ===
    undo_gura, _ = demo.say_hi_to('Gura')
    undo_bloop, _ = demo.say_hi_to('Bloop')

    undo_gura()  # undo second last instead of last: (2) [Gura, Bloop] -> (1) [Bloop]
    print('stack15:', len(demo._undo_stack), '; hihi15:', demo.hihi)  # stack15: 1 ; hihi15: [['Hi', 'Bloop']]
    print('stack16:', demo.undo(), '; hihi16:', demo.hihi)  # stack16: 0 ; hihi16: []

    demo.say_hi_to('Gura')
    demo.say_hi_to('Bloop')
    demo.purge_undo(purge_all=False)  # purge last undo: (2) [Gura, Bloop] -> (1) [Gura]
    print('stack17:', demo.undo(), '; hihi17:', demo.hihi)  # stack17: 0 ; hihi17: [['Hi', 'Bloop']]

    # === [Advanced] Memory Check ===
    # FIXME: Uncomment following code to check if garbage collection gets invoked as expected (otherwise memory leaks)
    # memcheck_func = UndoAbleFunc()
    # memcheck_purge = UndoAbleFunc()
    # while True:
    #     memcheck_instance = UndoAbleFunc()
    #
    #     for i in range(620):
    #         memcheck_instance.say_hi_to('Party Horns')  # ref_instance stay still (auto garbage collected)
    #
    #         memcheck_func.say_hi_to('Trident')
    #         memcheck_func.undo()  # reduce ref_func (undo_stack) & gc_count (hihi)
    #
    #         undo, _ = memcheck_func.say_hi_to('Floaties')
    #         undo()  # reduce ref_func (undo_stack) & gc_count (hihi)
    #
    #         memcheck_purge.say_hi_to('padowo')
    #         memcheck_purge.purge_undo()  # reduce ref_purge (undo_stack) but the gc_count (hihi) keeps growing
    #     memcheck_purge.hihi.clear()  # reduce gc_count (hihi)
    #
    #     ref_instance, ref_func = sys.getrefcount(memcheck_instance), sys.getrefcount(memcheck_func)
    #     ref_purge, gc_count = sys.getrefcount(memcheck_purge), len(gc.get_objects())
    #     print(f'[Ref] Instance: {ref_instance}, Func: {ref_func: >2}, Purge: {ref_purge: >2}; GC: {gc_count: >5}')
