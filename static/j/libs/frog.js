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
    var Frog = {};
    if (typeof exports !== 'undefined') {
        if (typeof module !== 'undefined') {
            module.exports = Frog;
        }
        else {
            exports = Frog;
        }
    }
    else {
        global.Frog = Frog;
    }
    Ext.Loader.setConfig({
        enabled:true,
        paths: {
            'Ext': '/static/frog/j/extjs-4.1.0/src'
        }
    });

    Frog.pixel = null;
    Frog.user = null;
    // -- Set the loading image
    Frog.loading = new Image();
    Frog.loading.src = '/static/frog/i/loading.png';
    Frog.icon = function(icon) {
        return Frog.StaticRoot + '/frog/i/' + icon + '.png'
    }

    Frog.getPixel = function() {
        if (Frog.pixel === null) {
            Frog.pixel = '/static/frog/i/pixel.png';
        }

        return Frog.pixel;
    }
    Frog.util = {
        fitToRect: function(rectW, rectH, width, height) {
            var iratio = width / height;
            var wratio = rectW / rectH;
            var scale;

            if (iratio > wratio) {
                scale = rectW / width;
            }
            else {
                scale = rectH / height;
            }

            return {width: width * scale, height: height * scale};
        }
    }
    
    Frog.Prefs = {
        init: function() {
            new Request.JSON({
                url: '/frog/pref/',
                async: false,
                noCache: true,
                onSuccess: function(res) {
                    Object.append(this, res.value);
                }.bind(this)
            }).GET();
        },
        set: function(key, value, callback) {
            new Request.JSON({
                url: '/frog/pref/',
                noCache: true,
                async: false,
                headers: {"X-CSRFToken": Cookie.read('csrftoken')},
                onSuccess: function(res) {
                    Object.append(this, res.value);
                    if (callback) {
                        callback();
                    }
                }.bind(this)
            }).POST({key: key, val: value});
        }
    };

    new Request.JSON({
        url: '/frog/getuser',
        async: false,
        onSuccess: function(res) {
            if (res.isSuccess) {
                Frog.Prefs.init();
                Frog.user = true;
            }
            else {
                Object.append(Frog.Prefs, res.value);
            }
        }
    }).GET();

    Frog.TagManager = new Class({
        initialize: function() {
            this.tags = {};
            var self = this;
            
            new Request.JSON({
                url: '/frog/tag/',
                async: false,
                onSuccess: function(res) {
                    if (res.isSuccess) {
                        res.values.each(function(tag) {
                            self.tags[tag.id] = tag.name;
                        });
                    }
                    else if (res.isError) {
                        throw res.message;
                    }
                }
            }).GET({json:true});
        },
        get: function(arg) {
            var value;
            var self = this;
            if (typeOf(arg) === 'number') {
                value = this.tags[arg];
                if (!value) {
                    new Request.JSON({
                        url: '/frog/tag/' + arg,
                        async: false,
                        onSuccess: function(res) {
                            if (res.isSuccess) {
                                value = res.value.name;
                                self.tags[value] = res.value.name;
                            }
                        }
                    }).GET({json:true});
                }
            }
            else {
                arg = arg.toLowerCase();
                var idx = Object.values(this.tags).indexOf(arg);
                if (idx >= 0) {
                    value = Object.keys(this.tags)[idx].toInt();
                }
                else {
                    new Request.JSON({
                        url: '/frog/tag/',
                        async: false,
                        headers: {"X-CSRFToken": Cookie.read('csrftoken')},
                        onSuccess: function(res) {
                            if (res.isSuccess) {
                                value = res.value.id.toInt();
                                self.tags[value] = res.value.name;
                            }
                        }
                    }).POST({name: arg});
                }
            }
            
            return value;
        },
        getByName: function(name) {

        },
        getByID: function(id) {

        }
    });
    Frog.Tag = new Class({
        Implements: Events,
        initialize: function(id, name) {
            var self = this;
            this.id = id;
            this.name = name || Frog.Tags.get(id);
            this.isSearch = typeof(id) === 'string';
            this.element = new Element('li', {'class': 'frog-tag'});
            if (this.isSearch) {
                this.element.addClass('frog-tag-search');
            }
            this.element.dataset.frog_tag_id = this.id;
            new Element('span').inject(this.element);
            new Element('a', {href: 'javascript:void(0);', text: this.name.capitalize(), 'class': 'frog-tag'}).inject(this.element);
            this.closeButton = new Element('div', {
                text: 'x',
                events: {
                    'click': this.close.bind(this)
                }
            }).inject(this.element);
        },
        close: function(e) {
            this.fireEvent('onClose', [this]);
        },
        toElement: function() {
            return this.element;
        }
    })
    Frog.Tags = new Frog.TagManager();

    Frog.CommentManager = new Class({
        Implements: Events,
        initialize: function() {
            var self = this;
            this.container = new Element('div', {
                id: 'frog_comments_container',
                events: {
                    click: function(e) {
                        if (e.target === this) {
                            self.close();
                        }
                    }
                }
            }).inject(document.body);
            this.element = new Element('div', {id: 'frog_comments_block'}).inject(this.container);
            this.container.hide();
            this.saveButton = null;
            this.guid = '';
            this.request = new Request.HTML({
                url: '/frog/comment/',
                evalScripts: true,
                noCache: true,
                onSuccess: function(tree, elements, html) {
                    this.open(html);
                }.bind(this)
            });
            this.top = new Element('div').inject(this.element);
            var bot = new Element('div').inject(this.element);
            if (Frog.user !== null) {
                this.fakeInput = new Element('input', {
                    'placeholder': 'Comment...',
                    events: {
                        click: function(e) {
                            e.stop();
                            this.hide();
                            var el = $('frog_comments');
                            var guid = el.dataset.frog_guid;
                            var id = el.dataset.frog_gallery_id;
                            self.input.show();
                            self.input.focus();
                            if (!self.saveButton) {
                                self.saveButton = Ext.create('Ext.Button', {
                                    text: 'Save',
                                    renderTo: bot,
                                    handler: function() {
                                        new Request.JSON({
                                            url: '/frog/comment/'
                                        }).POST({guid: guid, comment: self.input.value});
                                        self.close();

                                        self.fireEvent('onPost', [id]);
                                    }
                                });
                                Ext.create('Ext.Button', {
                                    text: 'Cancel',
                                    renderTo: bot,
                                    handler: function() {
                                        self.close();
                                    }
                                })
                            }
                        }
                    }
                }).inject(bot);
            }
            
            
            this.input = new Element('textarea').inject(bot);
            this.input.hide();
            this.scrollEvent = function(e) {
                e.stop();
            }
        },
        get: function(guid, id) {
            this.guid = guid;
            this.request.GET({guid: guid, id: id});
        },
        open: function(html) {
            this.container.show();
            var expression = /[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?/gi;
            var regex = new RegExp(expression);
            var matches = html.match(regex);
            if (matches) {
                for (var i=0;i<matches.length;i++) {
                    var link = matches[i];
                    var a = '<a href="' + link + '" target="_blank">' + link + '</a>';
                    html = html.replace(link, a);
                }
            }
            this.top.set('html', html);
            window.addEvent('mousewheel', this.scrollEvent);
        },
        close: function() {
            this.container.hide();
            if (Frog.user !== null) {
                this.fakeInput.show();
            }
            
            this.input.value = "";
            this.input.hide();
            window.removeEvent('mousewheel', this.scrollEvent);
        }
    });
    Frog.Comments = new Frog.CommentManager();

})(window);