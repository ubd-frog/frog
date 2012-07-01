// Copyright (C) 2012 Brett Dixon

// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 
// "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject 
// to the following conditions:

// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO 
// THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
// SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN 
// ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE 
// USE OR OTHER DEALINGS IN THE SOFTWARE.

(function(root) {
    function recJSON(obj, root) {
        root = root || new Element('ul');
        switch (typeOf(obj)) {
            case 'array':
                obj.each(function(item, index) {
                    var el = new Element('li', {text: index});
                    el.addClass('rest-' + typeOf(item));
                    if (typeOf(item) === 'array' || typeOf(item) === 'object') {
                        recJSON(item).inject(el);
                        el.addClass('open');
                        el.addEvent('click', function(e) {
                            e.stop();
                            var t = e.target;
                            if (t.hasClass('open')) {
                                t.getChildren('ul').setStyle('display', 'none');
                                t.removeClass('open');
                                t.addClass('close');
                            }
                            else if (t.hasClass('close')) {
                                t.getChildren('ul').setStyle('display', 'block');
                                t.addClass('open');
                                t.removeClass('close');
                            }
                        });
                    }
                    el.inject(root);
                });
                break;
            case 'object':
                Object.each(obj, function(val, key) {
                    var el = new Element('li', {text: key + ': ' + val});
                    el.addClass('rest-' + typeOf(val));
                    if (typeOf(val) === 'array' || typeOf(val) === 'object') {
                        el.set('text', key);
                        el.addClass('open');
                        recJSON(val).inject(el);
                        el.addEvent('click', function(e) {
                            e.stop();
                            var t = e.target;
                            if (t.hasClass('open')) {
                                t.getChildren('ul').setStyle('display', 'none');
                                t.removeClass('open');
                                t.addClass('close');
                            }
                            else if (t.hasClass('close')) {
                                t.getChildren('ul').setStyle('display', 'block');
                                t.addClass('open');
                                t.removeClass('close');
                            }
                        });
                    }
                    el.inject(root);
                });
                break;
            default:
                var el = new Element('li', {text: obj});
                el.inject(root);
                break;
        }

        return root;
    }
    function getRequest() {
        var main = document.id('main');
        var options = {
            url: document.id('url').value,
            emulation: false,
            noCache: true,
            onSuccess: function(res) {
                try {
                    var data = JSON.parse(res);
                    main.empty();
                    var el = recJSON(data);
                    el.inject(main);
                    
                }
                catch (e) {
                    main.set('html', res);
                }
            },
            onFailure: function(res) {
                main.set('html', "<pre>" + res.responseText + "</pre>");
            },
            onException: function(res) {
                main.set('html', "<pre>" + res.responseText + "</pre>");
            }
        }
        var data = {};
        $$('.data-row').each(function(row) {
            var key = row.firstChild.value;
            var val = row.lastChild.value;
            if (key !== '') {
                data[key] = val;
            }
        })
        return [new Request(options), data];
    }
    root.addEvent('domready', function() {
        document.id('get').addEvent('click', function() {
            var r = getRequest()
            r[0].GET(r[1]);
        });
        document.id('post').addEvent('click', function(e) {
            e.stop();
            var r = getRequest()
            r[0].POST(r[1]);
        });
        document.id('put').addEvent('click', function() {
            var r = getRequest()
            r[0].PUT(r[1]);
        });
        document.id('del').addEvent('click', function() {
            var r = getRequest()
            r[0].DELETE(r[1]);
        });

        for (var i=0;i<localStorage.length;i++) {
            var item = localStorage.key(i);
            if (item.contains('key')) {
                var idx = item.replace(/key/i, '');
                if (idx === "1") {
                    continue;
                }
                var div = new Element('div', {'class': 'data-row'});
                new Element('input', {type: 'text', name: 'key' + idx, value: localStorage[item]}).inject(div);
                new Element('span', {text: ' : '}).inject(div);
                new Element('input', {type: 'text', name: 'val' + idx, value: localStorage['val' + idx]}).inject(div);
                new Element('div', {
                    'class': 'removeRow',
                    events: {
                        'click': function() {

                        }
                    }
                });//.inject(div);
                div.inject(document.id('data'));
            }
        }

        $$('input[type=text]').each(function(item) {
            item.addEvent('keyup', function() {
                if (item.value === "") {
                    localStorage.removeItem(item.name);
                }
                else {
                    localStorage.setItem(item.name, item.value);
                }
            });
            var val = localStorage.getItem(item.name);
            if (val) {
                item.value = val;
            }
        });

        $$('.data-row input:last-child').getLast().addEvent('keydown', function(e) {
            if (e.code === 9) {
                e.stop();
                // Tab
                var idx = $$('.data-row').length + 1;
                var newEl = this.parentNode.clone().inject(this.parentNode, 'after');
                newEl.firstChild.value = '';
                newEl.firstChild.name = 'key' + idx;
                newEl.firstChild.focus();
                newEl.lastChild.value = '';
                newEl.lastChild.name = 'val' + idx;
                new Element('div', {
                    'class': 'removeRow',
                    events: {
                        'click': function() {

                        }
                    }
                });//.inject(newEl);
                newEl.getChildren().each(function(item) {
                    item.addEvent('keyup', function() {
                        if (item.value === "") {
                            localStorage.removeItem(item.name);
                        }
                        else {
                            localStorage.setItem(item.name, item.value);
                        }
                    });
                });
            }
        })
    });
})(window);
