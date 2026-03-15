/* is it better to use `x.hasOwnProperty(y)` `typeof x.y == "undefined"`? */
if (typeof Element.prototype.append == "undefined") {
    Element.prototype.append = function() {
        var i;
        for (i = 0; i < arguments.length; i++) {
            var thing = arguments[i];
            if (typeof thing == "string") {
                this.appendChild(document.createTextNode(thing));
            } else if (thing instanceof Node) {
                this.appendChild(thing);
            } else {
                console.log("cannot appendChild(" + thing + ")");
            }
        }
    };
}
/* vim: set tabstop=8 shiftwidth=4 expandtab softtabstop=4: */
