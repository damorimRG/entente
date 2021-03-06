// Copyright (C) 2011 the V8 project authors. All rights reserved.
// This code is governed by the BSD license found in the LICENSE file.
/*---
es6id: B.3.3
description: >
    redeclaration within block:
    attempt to redeclare let binding with function declaration
negative:
  phase: parse
  type: SyntaxError
---*/

// throw "Test262: This statement should not be evaluated.";
{ let f; function f() {} }
