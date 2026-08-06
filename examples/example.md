# Malange

Malange is a full stack generalized application framework for
developing various types of application with Python and easy to 
use templating language. Malange is open source and is licensed in 
MIT License.

## Architecture

At its base, Malange is composed of several components:
- Engine: The engine is responsible for processing the template language (```.mala```)
- Middle: The middle is responsible for processing middlewares.
- Gateway: The gateway is responsible for yielding whatever app you wish for.

Let's assume a Python frontend web application:
- The gateway will tell the bindings, DOM APIs, etc.
- The engine will link the utilities of the gateway to be used by you in the template.
- The middle can intercept. But they must "understand" both the gateway and the core.

This means the ecosystem of Malange is open-ended. Thus, boilerplate components are included.

## Boilerplate

The initial goal of Malange will aim for web development with a simple WSGI-compatible gateway that
allows for bringing frontend development to Malange. Why not backend too? Because backend web development 
is already within the reach of Python, we focus on the full stack aspect first.

## Syntax

There are elements and blocks. Elements are HTML-like syntax you use to build your graphical
components. Malange chooses the approach of Svelte when it comes to the syntax.

```mala
<p>Hello, my name is John Doe.</p>
```

Then there are blocks, syntax that are provided by Malange.

```mala
[opening tag/]

[/middle tag/]

[/closing tag]
```

There is also self-closing blocks, which can be made with one middle tag.

```mala
[/middle tag/]
```

There are also "specials", a group of syntax that are not blocks, but nevertheless
are part of Malange template syntax.

### Script Block

The first is the ```[script]``` tag, which allows you to use Python in the frontend.

```mala
[script/]
name = "John Doe"
[/script]

<p>Hello, my name is ${name}.</p>
```

Note that indentation still matters. If you notice, ```name = "John Doe"```
has no indentation. You can also outsource the script to a seperate file.

```mala
[/script src="./source.py"/]

<p>Hello, my name is ${name}.</p>
```

### Injection Special

The second is what is called an injection special. It will only
accept value yielded by ONE expression. The expression can be anything,
but there can only be one.

The notation is ```${ ... }```.


```mala
[script/]
name = "John Doe"

def addr():
    if name == "John Doe":
        return "yes"
[/script]

<p>Hello, my name is ${name}.</p>
<p>Am I good? The answer is ${addr()}.</p>
```

If there is no value being yielded, it will return nothing.

### Action Special

The third is what is called an action special. An action special allows you
to easily tie an element to a Python function. In web development, this can be
useful for easy DOM manipulation without the hassle of Vanilla DOM APIs.

The syntax is ```@{ ... }```

```mala
[script/]
from malange_core.api.engine import react
from malange_web import bind

name  = "John Doe"
agree = react(False)
[/script]

<p>Hello, my name is ${name}.</p>

<form>
    <input type="checkbox" @{bind.checked(agree)}>
    <p>I agree that I am a valid user.</p>
</form>
```

### For Block

For block allows for repeating rendering.

```mala
[script/]
name  = ["John Doe", "Dwayne Johnson", "Steve Haynes", "Robert Keys"]
[/script]

[for person in name/]

<p>${person}</p> <!-- Use injection to embed index variable of the list -->

[/for]
```

### If Block

If block allows for conditional rendering.

```mala
[if expression_1/]

<result_1>

[/elif expression_2/]

<result_2>

[/else/]

<result_3>

[/if]
```

The rule is:
- Mutliple elifs are allowed. Elifs are optional in the first place.
- Else is also optional, but there can only be one.
- If is mandatory.

### Switch Block

Switch block is an alternative to if for conditional rendering.

```mala
[switch variable/]

[/case value_1/]

<result_1>

[/case value_2/]

<result_2>

[/case _/] <!-- This is default case -->

<result_default>

[/switch]
```

The switch block is adapted from switch-case system.
