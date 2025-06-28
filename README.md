# Malange

An open-source application framework for developing apps.

```malange
# Example for Malange code that shows event listening.
# This example is for developing web application.

[script]

from malange.types import HTMLObject

$text: str = ""
$button_color: str = "red"

def show_text(event: HTMLObject.event):
		text = "Hello, my name is Malange!"
		button_color = "green"

[/script]

<p>${text}</p>

<button class="btn" @click={show_text(event)}>Click me!</button>

<style>

.btn {
		color : ${button_color};
};

</style>
```

The general goal of Malange is that rather than creating yet another
app framework is to combine frontend and backend development in a full-stack
manner. One language, one framework, one system.
