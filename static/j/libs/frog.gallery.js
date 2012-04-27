

Frog.Gallery = new Class({
    Implements: [Events, Options],
    options: {},
    initialize: function(el, options) {
        this.setOptions(options);
        this.el = (typeof el === 'undefined' || typeOf(el) === 'null') ? $(document.body) : $(el);
        this.container = new Element('div', {
            id: 'gallery'
        }).inject(this.el);

        this.tilesPerRow = 2;
        this.tileSize = (window.getWidth() - 2) / this.tilesPerRow;

        this.objects = [];
        this.thumbnails = [];
        this.y = 0;
        this.timer = this._scrollTimer.periodical(300, this);
        this.dirty = true;
        this.requestValue = {};
        this.isRequesting = false;        

        window.addEvent('scroll', this._scroll.bind(this));
        window.addEvent('resize', this.resize.bind(this));
        this.container.addEvent('click:relay(a)', function(e, el) {
            console.log(el.dataset.frog_tag_id);
        });
    },
    clear: function() {
        this.objects = [];
        this.container.empty();
    },
    request: function(append) {
        if (this.isRequesting) {
            return;
        }
        append = (typeof(append) === 'undefined') ? false : append;
        var data = (append) ? {more: true} : {};
        var self = this;
        new Request.JSON({
            url: '/frog/gallery/1/filter',
            onRequest: function() {
                self.isRequesting = true;
            },
            onSuccess: function(res) {
                //console.log(res)
                self.requestValue = res.value;
                if (res.isSuccess) {
                    if (!append) {
                        self.clear();
                    }
                    res.values.each(function(o) {
                        self.objects.push(o);
                        var t = new Frog.Thumbnail(self.objects.length - 1, o.width, o.height, {
                            title: o.title,
                            artist: o.author.first + ' ' + o.author.last,
                            tags: o.tags,
                            image: o.thumbnail,
                            imageID: o.id,
                            onSelect: function() {
                                this.element.addClass('selected')
                            }
                        });
                        self.thumbnails.push(t);
                        t.setSize(self.tileSize);
                        self.container.grab($(t));
                    });
                    self._getScreen();
                }
                self.isRequesting = false;
            }
        }).GET(data);
    },
    resize: function() {
        this.tileSize = (window.getWidth() - 2) / this.tilesPerRow;
        this.thumbnails.each(function(t) {
            t.setSize(this.tileSize);
        }, this)
    },
    _getScreen: function() {
        var s, e, t, row, endRow;

        row = Math.floor(window.getScroll().y / (this.tileSize + 30));
        s = row * this.tilesPerRow;
        endRow = row + Math.floor(window.getHeight() / (this.tileSize + 30));
        e = endRow * this.tilesPerRow + this.tilesPerRow;

        for (var i=s;i<e;i++) {
            t = this.thumbnails[i]
            if (t) {
                t.load();
                $(t).addClass('loaded');
            }
        }

        this.dirty = false;
    },
    _scroll: function () {
        clearTimeout(this.timer);
        this.timer = this._scrollTimer.periodical(300, this);
        this.dirty = true;
        var heightDelta = this.container.getHeight() - window.getScroll().y;
        var buffer = 300;
        
        if (heightDelta < window.getHeight() + buffer && this.requestValue.count > 0) {
            this.request(true)
        }
    },
    _scrollTimer: function() {
        if (this.dirty) {
            this._getScreen();
        }
    }
})