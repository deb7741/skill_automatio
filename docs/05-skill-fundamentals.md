# 05 · SKILL fundamentals

SKILL is a Lisp dialect with an optional C-like syntax. You type it into the **CIW** (Command Interpreter Window), put it in `.cdsinit`, or load it from files (`.il` for SKILL, `.ils` for SKILL++).

## 1. Getting help inside Virtuoso

| Where | How |
|---|---|
| SKILL API Finder | CIW → **Tools → SKILL API Finder**: search every documented function |
| SKILL IDE | CIW → **Tools → SKILL IDE**: editor, breakpoints, step, watch |
| Quick help | `help('dbOpenCellViewByType)` in the CIW (where available) |
| What does an object have? | `obj~>?` lists attributes, `obj~>??` lists attributes + values |
| Reverse engineering | Do an action in the GUI, then read `CDS.log` to see which SKILL ran |

> The last one is the single most useful SKILL learning trick. **CIW → Options → Log Filter** controls how much gets echoed.

## 2. Syntax: two styles, same language

```lisp
; C-like (algebraic) style — most common in Virtuoso code
x = 3
printf("x+1 = %d\n" x + 1)
if( x > 2 then println("big") else println("small"))

; Lisp style — identical meaning
(setq x 3)
(printf "x+1 = %d\n" (plus x 1))
(if (greaterp x 2) (println "big") (println "small"))
```

**Important:** in C-style, there must be **no space between a function name and its `(`**. `printf ("hi")` is parsed differently from `printf("hi")`.

## 3. Data types

| Type | Example | Test |
|---|---|---|
| Integer | `42` | `integerp` / `fixp` |
| Float | `1.5`, `1e-9`, scaled `1n`, `10k` | `floatp` |
| String | `"hello"` | `stringp` |
| Symbol | `'tran`, `'myVar` | `symbolp` |
| List | `list(1 2 3)`, `'(1 2 3)` | `listp` |
| `nil` / `t` | false/empty list, true | `null` |
| Database object | `dbObject` from `dbOpenCellViewByType` | `dbobjectp` |
| Association table | `makeTable("t" nil)` | `tablep` |
| Port (file) | `outfile("x.txt")` | `portp` |
| Function object | `'myFunc`, `lambda((x) x*x)` | `functionp` |

Scaled numbers (`1k`, `2.5n`, `3M`) work in SKILL. Note that **`M` = mega** here.

## 4. Lists: the core data structure

```lisp
l = list("a" "b" "c")
car(l)          ; "a"        (first)
cdr(l)          ; ("b" "c")  (rest)
cadr(l)         ; "b"        (second)
nth(2 l)        ; "c"        (zero-based)
length(l)       ; 3
append(l '("d")); ("a" "b" "c" "d")
cons("z" l)     ; ("z" "a" "b" "c")   — fast prepend
reverse(l)
member("b" l)   ; ("b" "c")  (non-nil = found)
sort(copy(l) 'alphalessp)

; Disembodied property list (handy "struct")
p = list(nil 'name "R1" 'value 1k)
p->name         ; "R1"
p->value = 2k
```

### Iteration and higher-order functions

```lisp
foreach(x l printf("%s\n" x))                 ; loop
foreach(mapcar x l strcat(x "_new"))          ; collect results
mapcar(lambda((x) upperCase(x)) l)
setof(x l x != "b")                           ; filter → ("a" "c")
exists(x l x == "b")                          ; first match tail, or nil
forall(x l stringp(x))                        ; t if all true
for(i 0 9 printf("%d " i))
while(cond ...)
```

## 5. Variables and functions

```lisp
procedure(vagAdd(a b "nn")       ; "nn" = argument type template: number number
  a + b)

procedure(vagGreet(name @optional (greeting "Hello") @key (punct "!"))
  sprintf(nil "%s, %s%s" greeting name punct))

vagGreet("Ana")                         ; "Hello, Ana!"
vagGreet("Ana" "Hi" ?punct ".")         ; "Hi, Ana."

procedure(vagSum(@rest nums)
  let((total)
    total = 0
    foreach(n nums total = total + n)
    total))
```

- **Always use `let()`** (or `prog()` if you need `return()`/`go`) to keep variables local. Undeclared variables are **global** and will collide with other people's code.
- **Prefix all globals** (functions and variables) with something unique: `vag`, your initials, your team. Cadence reserves lowercase prefixes like `db`, `sch`, `le`, `hi`, `ge`, `axl`, `mae`, `asi`, `ocn`.

```lisp
procedure(vagFindFirstNeg(lst)
  prog((result)
    foreach(x lst
      when(x < 0 result = x return(result)))
    return(nil)))
```

## 6. Control flow

```lisp
if(cond then a else b)
when(cond a b c)                 ; if-true, multiple forms
unless(cond a b c)
cond(
  (x < 0  "neg")
  (x == 0 "zero")
  (t      "pos"))
case(type
  ("tran" 1)
  (("ac" "noise") 2)
  (t 0))
caseq(sym ('a 1) ('b 2) (t 0))   ; for symbols/integers, faster
```

## 7. Strings

```lisp
sprintf(nil "%s_%03d" "cell" 7)        ; "cell_007"
strcat("a" "b" "c")                    ; "abc"
strlen("abc")                          ; 3
substring("abcdef" 2 3)                ; "bcd"   (1-based start, length)
parseString("a,b,,c" ",")              ; ("a" "b" "c")
buildString('("a" "b" "c") "/")        ; "a/b/c"
upperCase("x")  lowerCase("X")
index("abc" "b")                       ; "bc"
rexCompile("^vdd") rexExecute("vdd!")  ; POSIX-like regex
pcreMatchp("^net[0-9]+$" "net12")      ; PCRE regex (IC6.1.6+)
atoi("42") atof("1.5") evalstring("1k*2")
aelNumber("1.5u")                      ; parse scaled string → 1.5e-06
```

## 8. Files and the shell

```lisp
; write
p = outfile("/tmp/out.txt" "w")      ; "a" to append
fprintf(p "%s,%g\n" "bw" 1.2e6)
close(p)

; read line by line
p = infile("/tmp/out.txt")
when(p
  while(gets(line p) printf("%s" line))
  close(p))

isFile("x") isDir("y") createDir("z") deleteFile("x")
getDirFiles("/some/dir")
simplifyFilename("~/a/../b")
getShellEnvVar("HOME") setShellEnvVar("FOO=bar")

; run a shell command
system("ls -l > /tmp/ls.txt")                   ; blocking, returns exit status
csh("echo hi")  sh("echo hi")                   ; blocking, returns t/nil
pid = ipcBeginProcess("sleep 2; echo done")     ; non-blocking
ipcWait(pid)  ipcReadProcess(pid)
```

`ipcBeginProcess` with data/exit callbacks is the way to launch long external jobs (Python, simulators) without freezing the GUI.

## 9. Association tables (hash maps)

```lisp
tbl = makeTable("cellCounts" 0)     ; default value 0
tbl["inv"] = tbl["inv"] + 1
foreach(k tbl printf("%s -> %d\n" k tbl[k]))
tbl~>?                               ; list keys
```

## 10. Error handling and debugging

```lisp
; catch errors instead of aborting the whole script
res = errset(1/0 t)          ; nil on error; t = print the error message
unless(res warn("division failed\n"))

; raise errors
error("vagCheck: cell %s not found\n" cellName)
warn("something odd\n")

; tracing
tracef(vagAdd)  untrace(vagAdd)
installDebugger()            ; or use the SKILL IDE
```

Check code quality with **SKILL Lint** (`sklint(?file "myfile.il")`, or from the SKILL IDE). It flags undeclared globals, wrong argument counts and unused variables.

## 11. Loading code

```lisp
load("file.il")       ; stop on error
loadi("file.il")      ; ignore errors, continue (good for .cdsinit)
loadContext("x.cxt")  ; compiled contexts (advanced)
```

Loading companion files reliably: SKILL has no portable "directory of this script", so point an environment variable at your SKILL folder (set it in your setup script):

```lisp
let((skillDir)
  skillDir = getShellEnvVar("VAG_SKILL_DIR")      ; e.g. /path/to/repo/examples/skill
  if(skillDir
    load(strcat(skillDir "/lib_utils.il"))
    warn("VAG_SKILL_DIR is not set\n")))
```

## 12. SKILL++ in one paragraph

Files ending in `.ils` (or code inside `inScheme()` / `toplevel('ils ...)`) use **SKILL++** semantics: lexical scoping, closures and Scheme-style namespaces. This lets you write modules with private state:

```lisp
; counter.ils
let((count)
  count = 0
  globalProc(vagNextId() count = count + 1))
```

Use SKILL++ for libraries of utilities; plain SKILL is fine for scripts.

## 13. Style guide (short)

1. Prefix everything global (`vag...`).
2. Local variables via `let`.
3. One function, one job; return `nil` on failure, a value on success.
4. Never modify a cellview you didn't open in `"a"`/`"w"` mode; always `dbSave` + `dbClose`.
5. Comment the release you tested with.

Next: [06 · SKILL for design automation](06-skill-design-automation.md)
