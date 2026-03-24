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
if (typeof String.prototype.padStart == "undefined") {
    String.prototype.padStart = function(count, padding) {
        padding = padding || " ";
        var padLength = count - this.length;
        var self = String(this);
        return padLength > 0 ?
            padding.repeat(padLength).slice(0, padLength) + self:
            self;
    }
};
if (typeof String.prototype.padEnd == "undefined") {
    String.prototype.padEnd = function(count, padding) {
        padding = padding || " ";
        var padLength = count - this.length;
        var self = String(this);
        return padLength > 0 ?
            self + padding.repeat(padLength).slice(0, padLength):
            self;
    }
};
/* vim: set tabstop=8 shiftwidth=4 expandtab softtabstop=4: */
