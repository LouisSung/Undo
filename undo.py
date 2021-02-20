import gc
import sys
from typing import Callable, List, Optional, Tuple


class UndoAble:
    def __init__(self):
        self._undo_stack: List[Tuple[Callable, Callable]] = []
        self._counter_uncommitted_undo = 0

    def undo(self, undo_all: bool = False, undo_n_times: int = 1) -> int:
        """[Usage] undo(): undo 1 time; undo(True): undo ALL; undo(False, 5): undo 5 times"""
        if len(self._undo_stack) == 0 or undo_n_times < 1:
            return -1  # nothing to undo
        else:
            actual_undo_times = len(self._undo_stack) if undo_all else min(undo_n_times, len(self._undo_stack))
            for _ in range(actual_undo_times):  # undo n times
                (self._undo_stack.pop()[0])()  # i.e., undo_one_commit()
            return len(self._undo_stack)

    def purge_undo(self) -> int:
        """[Usage] purge_undo(): purge ALL"""
        if len(self._undo_stack) == 0:
            return -1  # nothing to purge
        else:
            while self._undo_stack:  # purge all
                (self._undo_stack.pop()[1])()  # i.e., purge_one_commit()
            return 0  # i.e.. len(self._undo_stack), should ALWAYS be 0

    def add_undo(self, thing_to_undo: Callable, purge_callback: Callable = lambda: None):
        """[Usage] add_undo(lambda_func_for_undo, lambda_callback_for_purge = do_nothing_by_default)"""
        self._undo_stack.append((thing_to_undo, purge_callback))
        self._counter_uncommitted_undo += 1
        print(f'[Add Undo] stack {len(self._undo_stack)}, uncommitted undos {self._counter_uncommitted_undo}')

    def commit_undo(self, additional_undo_callback: Optional[Callable] = None,
                    additional_purge_callback: Optional[Callable] = None):
        """Group multiple added undo funcs as a single commit. An additional callback could be provided"""
        pack_to_undo = self._undo_stack[-self._counter_uncommitted_undo:]  # group last k uncommitted undos from stack
        pack_to_undo.reverse()  # reverse the pack for the later invoke
        del self._undo_stack[-self._counter_uncommitted_undo:]  # remove these k undos from stack

        # invoke undo and purge callbacks in the pack
        undo_callbacks = lambda: [(undo[0])() for undo in pack_to_undo]
        purge_callbacks = lambda: [(purge[1])() for purge in pack_to_undo]

        # add additional callbacks to the pack if provided
        actual_undo_callbacks = undo_callbacks if additional_undo_callback is None else (
            lambda: [undo() for undo in [undo_callbacks, additional_undo_callback]]
        )
        actual_purge_callbacks = purge_callbacks if additional_purge_callback is None else (
            lambda: [purge() for purge in [purge_callbacks, additional_purge_callback]]
        )

        self._undo_stack.append((actual_undo_callbacks, actual_purge_callbacks))
        self._counter_uncommitted_undo = 0
        print(f'[Commit Undo] stack: {len(self._undo_stack)}, undo pack: {len(pack_to_undo)}')


class UndoableClass(UndoAble):
    def __init__(self):
        super().__init__()
        self.hihi: List[List[str]] = []

    def say_hi_to(self, name: str) -> List[str]:
        debug = print  # change as `lambda log: None` to disable printing

        # === Start Doing Stuff ===
        hi_list: List[str] = []
        self.hihi.append(hi_list)
        self.add_undo(lambda: debug('undo `1. result`') or self.hihi.pop(), lambda: debug('purge `1. result`'))

        hi_list.append('Hi')
        self.add_undo(lambda: debug(f'undo `2. hi`: {hi_list}') or hi_list.pop(), lambda: debug('purge `2. hi`'))
        hi_list.append(name)
        self.add_undo(lambda: debug(f'undo `3. name`: {hi_list}') or hi_list.pop(), lambda: debug('purge `3. name`'))
        # # === End Doing Stuff ===

        # group those added undos as a commit_pack
        self.commit_undo(lambda: debug('undo `4. commit`'), lambda: debug('purge `4. commit`'))
        return hi_list


if __name__ == '__main__':
    demo = UndoableClass()
    # === [Basic] Undo ===
    result = demo.say_hi_to('Gura')  # use _ to consume useless undo
    print('hihi01:', demo.hihi, '; result:',  result)  # hihi01: [['Hi', 'Gura']] ; result: ['Hi', 'Gura']
    demo.undo()
    print('hihi02:', demo.hihi)  # hihi02: []

    demo.say_hi_to('A')
    demo.say_hi_to('SHAAAAAARK')
    demo.say_hi_to('MEATLOAF')
    print('hihi03:', demo.hihi)  # hihi03: [['Hi', 'A'], ['Hi', 'SHAAAAAARK'], ['Hi', 'MEATLOAF']]

    print('stack01:', demo.undo())  # stack01: 2 (undo the last one (M): [A, S, M](3) -> [A, S](2) => 2)
    print('hihi04:', demo.hihi)  # hihi04: [['Hi', 'A'], ['Hi', 'SHAAAAAARK']]
    print('stack02:', demo.undo(undo_all=True))  # stack02: 0 (undo all (S, A): [A, S](2) -> [](0) => 0)
    print('hihi05:', demo.hihi)  # hihi05: []
    print('stack03:', demo.undo())  # stack03: -1 (nothing to undo [](0) -> [](0) => -1)

    # === [Basic] Purge Undo ===
    demo.say_hi_to('Gawr')
    demo.say_hi_to('Gura')
    print('stack04:', len(demo._undo_stack), '; hihi06:', demo.hihi)  # stack04: 2 ; hihi06: [[...], [...]]
    print('stack05:', demo.purge_undo(), '; hihi07:', demo.hihi)  # stack05: 0 ; hihi07: [[...], [...]]
    print('stack06:', demo.purge_undo())  # stack06: -1 (nothing to undo)
    print('stack07:', demo.undo())  # stack07: -1 (nothing to undo)
    demo.hihi.clear()

    # === [Advanced] Memory Check ===
    # FIXME: Uncomment following code to check if garbage collection gets invoked as expected (otherwise memory leaks)
    # memcheck_func = UndoableClass()
    # memcheck_purge = UndoableClass()
    # while True:
    #     memcheck_instance = UndoableClass()
    #
    #     for i in range(620):
    #         memcheck_instance.say_hi_to('Floaties')  # ref_instance stay still (auto garbage collected)
    #
    #         memcheck_func.say_hi_to('Trident')
    #         memcheck_func.undo()  # reduce ref_func (undo_stack) & gc_count (hihi)
    #
    #         memcheck_purge.say_hi_to('padowo')
    #         memcheck_purge.purge_undo()  # reduce ref_purge (undo_stack) but the gc_count (hihi) keeps growing
    #     memcheck_purge.hihi.clear()  # reduce gc_count (hihi)
    #
    #     ref_instance, ref_func = sys.getrefcount(memcheck_instance), sys.getrefcount(memcheck_func)
    #     ref_purge, gc_count = sys.getrefcount(memcheck_purge), len(gc.get_objects())
    #     print(f'[Ref] Instance: {ref_instance}, Func: {ref_func: >2}, Purge: {ref_purge: >2}; GC: {gc_count: >5}')
