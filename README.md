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

## Example

Assume using ```malange_web```, this is a counter that can go up and down:

```mala
[script/]
from malange_core.api.engine import react
from malange_web.api.dom import on

counter = react(0, int)

def change(num: int) -> None:
    counter += num
[/script]

<p>The current value is: ${counter}.</p>

<div class="">
    <button @{on.click(change(+1))}>Add</button>
    <button @{on.click(change(-1))}>Substract</button>
</div>

```