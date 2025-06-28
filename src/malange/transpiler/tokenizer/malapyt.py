'''

    malange.transpiler.tokenizer.malapyt

    malapyt = Malange Python Tokenizer

    Manages the tokenization of Malange custom Python language.
    There will be modes for tokenization.

    First one is mode 'default', aka your typical 

    - MALANGE_BRAC_MID      [/ # Required for the detection of ending script tag.

    - PYTHON_WS_GEN         Generic whitespace: space and tab.
    - PYTHON_WS_NL          cr ln ln cr # Any kind of new line.

    - PYTHON_CURV_LEFT      (    PYTHON_CURV_RIGHT     )    
    - PYTHON_SQUR_LEFT      [    PYTHON_SQUR_RIGHT     ]
    - PYTHON_CURL_LEFT      {    PYTHON_CURL_RIGHT     }

    - PYTHON_POINT_DOT      .    PYTHON_POINT_COMMA    ,
    - PYTHON_POINT_COLON    :    PYTHON_POINT_SCOLON   ;

    - PYTHON_OP_PLUS        +    PYTHON_OP_MINUS       -
    - PYTHON_OP_STAR        *    PYTHON_OP_SLASH       /
    - PYTHON_OP_DTAR        **   PYTHON_OP_DSLASH      //
    - PYTHON_OP_TILDE       ~    PYTHON_OP_CARET       ^
    - PYTHON_OP_AMPSAND     &    PYTHON_OP_GRAVE       `
    - PYTHON_OP_SLEFT       <<   PYTHON_OP_SRIGHT      >>
    
    - PYTHON_AS_DEFINE      =    PYTHON_AS_REACTIVE    $
    - PYTHON_AS_PLUS        +=   PYTHON_AS_MINUS       -=
    - PYTHON_AS_STAR        *=   PYTHON_AS_SLASH       /=
    - PYTHON_AS_DTAR        **=  PYTHON_AS_DSLASH      //=
    - PYTHON_AS_TILDE       ~=   PYTHON_AS_CARET       ^=
    - PYTHON_AS_AMPSAND     &=   PYTHON_AS_GRAVE       `=
    - PYTHON_AS_SLEFT       <<=  PYTHON_AS_SRIGHT      >>=

    - PYTHON_CP_EQUAL       ==   PYTHON_CP_NOEQUAL     !=
    - PYTHON_CP_LESSEQ      <=   PYTHON_CP_MOREEQ      >=
    - PYTHON_CP_LESS        <    PYTHON_CP_MORE        >

    - PYTHON_SPEC_QUOT      " '
    - PYTHON_SPEC_COM       #
    - PYTHON_SPEC_CONT      /
    
    - PYTHON_GEN_LITERAL    2323, DFDF, dfdsfs, fun_name, var_name, anything
    - PYTHON_GEN_REACTIVE   $
    - PYTHON_GEN_ARROW      ->
    - PYTHON_GEN_DECOR      @
    - PYTHON_GEN_PIPE       |
    - PYTHON_GEN_PERCENT    %

'''

