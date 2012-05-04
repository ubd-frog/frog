

Frog.Thumbnail = new Class({
    Implements: [Events, Options],
    Padding: 14,//(8 + 2 + 4) * 2, // 8 for the div padding and 2 for the img padding
    options: {
        image: Frog.getPixel(),
        video: null,
        tags: [],
        artist: null,
        title: '',
        imageID: 0,
        onClick: function(){},
        onSelect: function(){},
        onLoad: function(){}
    },
    initialize: function(id, width, height, options) {
        this.setOptions(options);
        this.id = id;
        this.width = width;
        this.height = height;
        this.loaded = false;

        this.dimension = {};

        this.tags = [];
        this.selected = false;

        this.build();
        this.options.tags.each(function(tag) {
            this.addTag(tag);
        }, this);
        if (this.options.artist !== null) {
            this.setArtist(this.options.artist);
        }
    },
    build: function() {
        var self = this;
        this.element = new Element('div', {
            'class': 'thumbnail',
            events: {
                click: function(e) {
                    if (e.target.get('tag') === 'div') {
                        self.setSelected();
                    }
                }
            }
        });
        if (Browser.ie) {

        }
        this.element.dataset.frog_tn_id = this.id;
        var top = new Element('div').inject(this.element);
        this.spacer = new Element('div', {styles: {
            width: '100%',
            height: 0
        }}).inject(top);
        this.imgLink = new Element('a', {
            href: '/frog/image/' + this.options.imageID,
            events: {
                click: function(e) {
                    e.stop();
                }
            }
        }).inject(top);
        this.img = new Element('img', {
            src: Frog.getPixel(),
            events: {
                load: function() {
                    self.fireEvent('onLoad', [this]);
                },
                click: function(e) {
                    self.fireEvent('onClick', [e]);
                }
            }
        }).inject(this.imgLink);

        var tags = new Element('div', {'class': 'tag-hover'})//.inject(this.element);
        this.tagList = new Element('div').inject(tags);

        var bot = new Element('div').inject(this.element);
        this.title = new Element('div', {'text': this.options.title}).inject(bot);
        var artistDiv = new Element('div', {'text': 'Artist: '}).inject(bot);
        this.artist = new Element('a', {'href': "javascript:void(0);"}).inject(artistDiv);
    },
    toElement: function() {
        return this.element;
    },
    setArtist: function(artist) {
        var id = Frog.Tags.get(artist);
        this.artist.set('text', artist);
        this.artist.dataset.frog_tag_id = id;
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
        this.selected = (typeof sel === 'undefined') ? !this.selected : sel;
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
        if (this.tagList.getElements('a').length > 0) {
            this.tagList.innerHTML += ', ';
        }
        var tag = Frog.Tags.get(id);
        var a = new Element('a', {'href': 'javascript:void(0);', text: tag, 'class': 'frog-tag'}).inject(this.tagList);
        a.dataset.frog_tag_id = id;
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
        this.img.src = this.options.image;
        this.loaded = true;
    }
})