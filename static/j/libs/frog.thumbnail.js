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


Frog.Thumbnail = new Class({
    Implements: [Events, Options],
    Padding: 14,//(8 + 2 + 4) * 2, // 8 for the div padding and 2 for the img padding
    options: {
        imageID: 0,
        onClick: function(){},
        onSelect: function(){},
        onLoad: function(){}
    },
    initialize: function(id, object, options) {
        this.setOptions(options);
        this.id = id;
        this.object = object;
        this.width = object.width;
        this.height = object.height;
        this.loaded = false;
        this.guid = this.object.guid;

        this.dimension = {};

        this.tags = [];
        this.selected = false;

        this.build();
        
        if (this.options.artist !== null) {
            this.setArtist(this.options.artist);
        }
        this.object.tags.each(function(tag) {
            this.addTag(tag);
        }, this);
    },
    build: function() {
        var self = this;
        this.element = new Element('div', {
            'class': 'thumbnail noselect',
            events: {
                click: function(e) {
                    if (e.target.get('tag') === 'div') {
                        self.setSelected();
                    }
                }
            }
        });
        if (Browser.ie) {
            this.element.setProperty('dataset-frog_tn_id', this.id);
            this.element.setProperty('dataset-frog_guid', this.guid);
        }
        else {
            this.element.dataset.frog_tn_id = this.id;
            this.element.dataset.frog_guid = this.guid;    
        }
        
        var top = new Element('div').inject(this.element);
        this.spacer = new Element('div', {styles: {
            width: '100%',
            height: 0
        }}).inject(top);
        var linkType = (this.guid.charAt(0) === '1') ? 'image' : 'video';
        this.imgLink = new Element('a', {
            href: '/frog/' + linkType + '/' + this.options.imageID,
            'class': 'frog-image-link',
            events: {
                click: function(e) {
                    //e.stop();
                }
            }
        }).inject(top);
        this.img = new Element('img', {
            src: Frog.getPixel(),
            unselectable: 'on',
            events: {
                load: function() {
                    self.fireEvent('onLoad', [this]);
                },
                click: function(e) {
                    self.fireEvent('onClick', [e]);
                }
            }
        }).inject(this.imgLink);

        var tags = new Element('div', {'class': 'tag-hover'});//.inject(this.element);
        this.tagList = new Element('div').inject(tags);

        var bot = new Element('div').inject(this.element);
        this.title = new Element('span', {'text': this.object.title}).inject(bot);
        var artistDiv = new Element('div', {'text': 'Artist: '}).inject(bot);
        this.artist = new Element('a', {'href': "javascript:void(0);", 'class': 'frog-tag'}).inject(artistDiv);
        var commentLink = new Element('div', {
            'class': 'frog-comment-bubble',
            text: this.object.comment_count,
            events: {
                click: function(e) {
                    e.stop();
                    Frog.Comments.get(self.object.guid, self.id);
                }
            }
        }).inject(bot);
    },
    toElement: function() {
        return this.element;
    },
    setArtist: function(artist) {
        var id = Frog.Tags.get(artist);
        this.artist.set('text', artist.capitalize());
        if (Browser.ie) {
            this.artist.setProperty('dataset-frog_tag_id', id);
        }
        else {
            this.artist.dataset.frog_tag_id = id;
        }
    },
    setSize: function(size) {
        var dim = Frog.util.fitToRect(size - this.Padding, size - this.Padding, this.width, this.height);
        this.element.setStyles({
            width: size,
            height: size + 30
        });
        this.imgLink.setStyles(dim);
        this.img.setStyles({
            width: dim.width - 6,
            height: dim.height - 6
        });
        this.spacer.setStyles({
            height: (size - dim.height - 10) / 2
        });
    },
    setSelected: function(sel) {
        this.selected = (typeof sel === 'undefined') ? !this.element.hasClass('selected') : sel;
        if (this.selected) {
            this.element.addClass('selected');
        }
        else {
            this.element.removeClass('selected');
        }
        this.fireEvent('onSelect', [this]);
    },
    addTag: function(id) {
        if (typeOf(id.id) !== 'undefined') {
            id = id.id;
        }
        var artistTagId = (Browser.ie) ? this.artist.getProperty('dataset-frog_tag_id') : this.artist.dataset.frog_tag_id;
        if (id.toString() === artistTagId) {
            return;
        }
        if (this.tagList.getElements('a').length > 0) {
            this.tagList.innerHTML += ', ';
        }
        var tag = Frog.Tags.get(id);
        var a = new Element('a', {'href': 'javascript:void(0);', text: tag.capitalize(), 'class': 'frog-tag'}).inject(this.tagList);
        if (Browser.ie) {
            a.setProperty('dataset-frog_tag_id', id);
        }
        else {
            a.dataset.frog_tag_id = id;
        }
        
        this.tags.push(id);
    },
    removeTag: function(tag) {
        var i;
        for (i=0;i<this.tags.length;i++) {
            if (tag === this.tags[i]) {
                break;
            }
        }

        return this.tags.splice(1, i);
    },
    load: function () {
        if (this.loaded) {
            return true;
        }
        this.img.src = this.object.thumbnail;
        this.loaded = true;
    }
})