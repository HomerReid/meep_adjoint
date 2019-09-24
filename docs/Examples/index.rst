=========================================
:py:mod:`meep_adjoint` example gallery
=========================================

-------------------
Operator precedence
-------------------


.. |LR| replace:: Left-to-right
.. |RL| replace:: Right-to-left


==========  ==========   ==============================  =============
Precedence  Operator     Description                     Associativity
==========  ==========   ==============================  =============
1           \::          Scope resolution                |LR|
----------  ----------   ------------------------------  -------------
2           ( )          Function call                   |LR|

            [ ]          Subscript

            .            Member access

            .{ }         Bit-field concatenation
----------  ----------   ------------------------------  -------------
3           \+           Unary plus                      |RL|

            \-           Unary minus

            !            Logical not

            ~            Bitwise not

            (|type|)     Type cast

            & (unary)    Address-of

            sizeof       Size-of
----------  ----------   ------------------------------  -------------

