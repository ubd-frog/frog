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
        },
        clamp: function(min, max, val) {
            var n = Math.max(min, val);
            n = Math.min(max, n);

            return n;
        },
        getData: function(element, key, defaultvalue) {
            var value;
            if (Browser.ie) {
                value = element.getProperty('data-' + key);
            }
            else {
                value = element.dataset[key];
            }

            return (typeof(value) === 'undefined') ? defaultvalue : value;
        },
        setData: function(element, key, value) {
            if (Browser.ie) {
                element.setProperty('data-' + key, value);
            }
            else {
                element.dataset[key] = value;
            }
        },
        isGuid: function(value) {
            return value.length === 14;
        },
        hashData: function() {
            var str = unescape(location.href.split('#')[1]);
            return (str !== 'undefined') ? JSON.parse(str) : {};
        }
    }
    
    Frog.Prefs = {
        init: function() {
            new Request.JSON({
                url: '/frog/pref/',
                noCache: true,
                onSuccess: function(res) {
                    Object.append(this, res.value);
                    Frog.GalleryObject.request();
                }.bind(this)
            }).GET();
        },
        set: function(key, value, callback) {
            new Request.JSON({
                url: '/frog/pref/',
                noCache: true,
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
        onSuccess: function(res) {
            if (res.isSuccess) {
                Frog.Prefs.init();
                Frog.user = true;
            }
            else {
                Object.append(Frog.Prefs, res.value);
            }
            Frog.Comments.build();
        }
    }).GET();

    Frog.TagManager = new Class({
        initialize: function() {
            this.tags = {};
            var self = this;
            
            new Request.JSON({
                url: '/frog/tag/',
                onSuccess: function(res) {
                    if (res.isSuccess) {
                        res.values.each(function(tag) {
                            self.tags[tag.id] = tag.name.toLowerCase();
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
                        onSuccess: function(res) {
                            if (res.isSuccess) {
                                value = res.value.name;
                                self.tags[value] = res.value.name.toLowerCase();
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
            Frog.util.setData(this.element, 'frog_tag_id', this.id);
            
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
            this.guid = '';
            this.bSave = null;
            this.bCancel = null;
            this.request = new Request.HTML({
                url: '/frog/comment/',
                evalScripts: true,
                noCache: true,
                onSuccess: function(tree, elements, html) {
                    this.open(html);
                }.bind(this)
            });
            this.scrollEvent = function(e) {
                e.stop();
            }
        },
        build: function() {
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
            
            this.top = new Element('div').inject(this.element);
            var bot = new Element('form').inject(this.element);
            if (Frog.user !== null) {
                this.fakeInput = new Element('input', {
                    'placeholder': 'Comment...',
                    events: {
                        click: function(e) {
                            e.stop();
                            this.hide();
                            
                            self.input.show();
                            self.input.focus();
                            if (self.bSave) {
                                self.bSave.show();
                                self.bCancel.show();
                            }
                            else {
                                self.bSave = Ext.create('Ext.Button', {
                                    text: 'Save',
                                    renderTo: bot,
                                    handler: function() {
                                        var el = $('frog_comments');
                                        self.guid = Frog.util.getData(el, 'frog_guid');
                                        var id = Frog.util.getData(el, 'frog_gallery_id');
                                        new Request.JSON({
                                            url: '/frog/comment/'
                                        }).POST({guid: self.guid, comment: self.input.value});
                                        self.close();

                                        self.fireEvent('onPost', [id]);
                                    }
                                });
                                self.bCancel = Ext.create('Ext.Button', {
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
            this.container.setStyle('top', window.pageYOffset);
        },
        close: function() {
            this.container.hide();
            if (this.bSave !== null) {
                this.bSave.hide();
                this.bCancel.hide();
            }
            
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
