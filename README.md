# Malange

An open-source application framework for developing apps.

```malange
# Example for Malange code that shows event listening.
# This example is for developing web application.

[script/]

from malange.types import HTMLObject
from malange.utils import Reactive

reactive = Reactive(root_object)

text         = reactive("")
button_color = reactive("red")

def show_text(event: HTMLObject.event):
		text.assign("Hello, my name is Malange!")
		button_color.assign("green")

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
