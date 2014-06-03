/*
Copyright (c) 2012 Brett Dixon

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

(function(global) {
    var Selection = new Class({
        Implements: [Options, Events],
        options: {
            color: [51, 153, 255],
            selector: 'body *',
            ignore: [],
            useCache: true,
            snap: 10,
            selectionClass: 'selected'
        },
        initialize: function(el, options) {
            this.setOptions(options);
            this.root = el || document;

            this.element = new Element('div', {id: 'selection-element'}).inject(document.body);
            this.element.setStyles({
                position: 'absolute',
                border: '1px solid rgb(' + this.options.color.join(',') + ')',
                background: 'rgba(' + this.options.color.join(',') + ',0.5)'
            });
            this.__hide();
            this.isMouseDown = false;
            this.isActive = false;
            this.__point = {x: 0, y: 0};
            this.__cache = [];
            this.__items = [];
            this.__rootStyles = {};

            this.up = this.__up.bind(this);
            this.down = this.__down.bind(this);
            this.move = this.__move.bind(this);

            this.__addClass();

            this.activate();
        },
        activate: function() {
            this.root.addEvent('mousedown', this.down);
            global.addEvent('mouseup', this.up);
            global.addEvent('mousemove', this.move);
        },
        deactivate: function() {
            this.root.removeEvent('mousedown', this.down);
            global.removeEvent('mouseup', this.up);
            global.removeEvent('mousemove', this.move);
        },
        getElements: function(e) {
            var coords = this.element.getCoordinates();
            var items = [];
            
            if (!this.options.useCache) {
                this.__processCache();
            }

            this._cache.each(function(el) {
                if (this.__intersect(coords, el[1])) {
                    items.push(el[0]);
                    el[0].addClass(this.options.selectionClass);
                }
                else if (el[0].hasClass(this.options.selectionClass) && !e.shift) {
                    el[0].removeClass(this.options.selectionClass);
                }
                
            }, this);

            return items;
        },
        __up: function(e) {
            e.preventDefault();
            this.isMouseDown = false;
            if (this.isActive) {
                this.__items = this.getElements(e);
                this.fireEvent('onComplete', [e, this.__items]);
            }
            
            this.__hide();
            this.__cache = [];
            this.__deactivate();

            return false;
        },
        __down: function(e) {
            if (!this.options.ignore.contains(e.target.get('tag').toLowerCase())) {
                e.preventDefault();
                this.isMouseDown = true;
                if (this.options.useCache) {
                    this.__processCache();
                }
                this.__activate();
                this.__point = {x: e.client.x, y: e.client.y};
                this.element.setStyles({
                    top: this.__point.y,
                    left: this.__point.x,
                    width: 0,
                    height: 0
                });

                return false;
            }
        },
        __move: function(e) {
            var x, y, w, h, dx, dy;
            if (this.isMouseDown) {
                dx = e.client.x - this.__point.x;
                dy = e.client.y - this.__point.y;
                var active = (Math.abs(dx) >= this.options.snap || Math.abs(dy) >= this.options.snap);
                if (!active) {
                    return false;
                }
                e.preventDefault();
                this.__show();
                this.isActive = true;
                if (dx > 0) {
                    x = this.__point.x;
                    w = dx
                }
                else {
                    x = this.__point.x + dx;
                    w = Math.abs(dx);
                }

                if (dy > 0) {
                    y = this.__point.y;
                    h = dy
                }
                else {
                    y = this.__point.y + dy;
                    h = Math.abs(dy);
                }

                this.element.setStyles({
                    top: y + window.scrollY,
                    left: x,
                    width: w,
                    height: h
                });

                this.fireEvent('onChange', [e, this.getElements(e)]);

                return false;
            }
        },
        __processCache: function() {
            var cache = [];
            $$(this.options.selector).each(function(el) {
                cache.push([el, el.getCoordinates()]);
            });

            this._cache = cache;
        },
        __show: function() {
            this.element.setStyle('display', 'block');
        },
        __hide: function() {
            this.element.setStyle('display', 'none');
        },
        __activate: function() {
            // this.__rootStyles = document.body.getStyles('cursor', '-webkit-user-select');
            // document.body.setStyles({
            //     cursor: 'arrow',
            //     '-webkit-user-select': 'none'
            // });
            document.body.addClass('noselect');
        },
        __deactivate: function() {
            this.isActive = false;
            document.body.removeClass('noselect');
            //document.body.setStyles(this.__rootStyles);
            //document.body.setStyle('-webkit-user-select', null);
        },
        __intersect: function (r1, r2) {
            return !(
                r2.left > r1.right || 
                r2.right < r1.left || 
                r2.top > r1.bottom ||
                r2.bottom < r1.top
            );
        },
        __addClass: function() {
            var el = new Element('style', {'type': 'text/css'});
            el.set('html', '.noselect {\
                -webkit-touch-callout: none;\
                -webkit-user-select: none;\
                -khtml-user-select: none;\
                -moz-user-select: none;\
                -ms-user-select: none;\
                user-select: none;\
            }');
            el.inject(document.head);
        }
    });

    global.Selection = Selection;
})(window);