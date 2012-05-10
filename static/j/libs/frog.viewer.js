

Frog.Viewer = new Class({
    Implements: Events,
    initialize: function() {
        this.origin = {x: 0, y: 0};
        this.xform = Matrix.I(3);
        this.main = Matrix.I(3);
        this.scaleValue = 1.0;

        this.objects = [];
        this.current = 0;
        this.isMouseDown = false;

        this.element = new Element('div', {id: 'frog_viewer'}).inject(document.body);
        this.canvas = new Element('canvas', {width: window.getWidth(), height: window.getHeight()}).inject(this.element);

        this.ctx = this.canvas.getContext('2d');
        this.image = new Image();
        this.image.onload = this._loadCallback.bind(this);

        this.events = {
            up: this.up.bind(this),
            down: this.down.bind(this),
            move: this.move.bind(this),
            zoom: this.zoom.bind(this)
        }

        this.canvas.addEvent('mousedown', this.events.down);
        window.addEvent('mouseup', this.events.up);
        window.addEvent('mousemove', this.events.move);
        window.addEvent('mousewheel', this.events.zoom);

        this.build();
    },
    toElement: function() {
        return this.element;
    },
    up: function(e) {
        this.isMouseDown = false;
        this.main = this.xform;
        this.canvas.removeClass('drag');
    },
    down: function(e) {
        if (e.event.button == 0) {
            this.isMouseDown = true;
            this.origin.x = e.client.x;
            this.origin.y = e.client.y;
            this.canvas.addClass('drag');
        }
    },
    move: function(e) {
        if (this.isMouseDown) {
            var x = e.client.x - this.origin.x;
            var y = e.client.y - this.origin.y;

            this.xform = Matrix.I(3).x(this.main);
            this.translate(x,y);

            this.render();
        }
    },
    zoom: function(e) {
        e.stop();
        var scaleValue = 1.0;
        if (e.wheel > 0) {
            scaleValue += 0.05;
        }
        else {
            scaleValue -= 0.05;
        }
        var x = e.client.x;
        var y = e.client.y;
        this.xform = Matrix.I(3).x(this.main);
        this.translate(-x, -y);
        this.scale(scaleValue, scaleValue);
        this.translate(x, y);
        this.main = this.xform;
        this.render();
    },
    build: function() {
        var controls = new Element('div', {id: 'frog_viewer_controls'});
        var buttons = new Element('ul').inject(controls);
        this.bPrev = new Element('li', {'class': 'frog-prev'}).inject(buttons);
        this.bNext = new Element('li', {'class': 'frog-next'}).inject(buttons);
        this.bOriginal = new Element('li', {'class': 'frog-original'}).inject(buttons);
        this.bWindow = new Element('li', {'class': 'frog-window'}).inject(buttons);
        this.bDownload = new Element('li', {'class': 'frog-download'}).inject(buttons);

        this.bPrev.addEvent('click', this.prev.bind(this));
        this.bNext.addEvent('click', this.next.bind(this));
        this.bOriginal.addEvent('click', this.original.bind(this));
        this.bWindow.addEvent('click', this.fitToWindow.bind(this));
        this.bDownload.addEvent('click', this.download.bind(this));

        controls.inject(this.element);

        this.bClose = new Element('div', {
            'class': 'frog-viewer-close',
            events: {
                click: this.hide.bind(this)
            }
        }).inject(controls)
    },
    clear: function() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    },
    render: function() {
        this.clear();
        
        this.ctx.drawImage(
            this.image, 
            this.xform.elements[2][0],
            this.xform.elements[2][1],
            this.xform.elements[0][0],
            this.xform.elements[1][1]
        );
    },
    center: function(scale) {
        scale = scale || 1.0;

        this.xform = $M([
            [this.image.width,0,0],
            [0,this.image.height,0],
            [0,0,1]
        ]);
        this.scale(scale, scale);
        var x = window.getWidth() / 2 - this.xform.elements[0][0] / 2;
        var y = window.getHeight() / 2 - this.xform.elements[1][1] / 2;
        this.translate(x, y);

        this.main = this.xform;

        this.render();

    },
    next: function() {
        var idx = this.current + 1;
        idx = (idx > this.objects.length - 1) ? 0 : idx;

        this.setIndex(idx);
    },
    prev: function() {
        var idx = this.current - 1;
        idx = (idx < 0) ? this.objects.length - 1 : idx;

        this.setIndex(idx);
    },
    original: function() {
        this.center();
    },
    fitToWindow: function() {
        var padding = 40;
        var scale = (window.getWidth() - padding) / this.image.width;
        // scale = (scale < 1.0) ? 1.0 : scale;

        this.center(scale);
    },
    download: function() {
        var guid = this.objects[this.current].guid;
        location.href = '/frog/download?guids=' + guid;
    },
    translate: function(x, y) {
        var m1, m2;

        m1 = $M([
            [1,0,0],
            [0,1,0],
            [x,y,1]
        ]);

        var m2 = this.xform.x(m1);
        this.xform = m2.dup();
    },
    scale: function(x, y) {
        var m1, m2;

        m1 = $M([
            [x,0,0],
            [0,y,0],
            [0,0,1]
        ]);

        m2 = this.xform.x(m1);
        this.xform = m2.dup();
    },
    setImage: function(img) {
        this.clear();
        this.image.src = img;
        if (this.image.complete) {
            this._loadCallback();
        }
    },
    setImages: function(images, id) {
        id = id || 0;
        this.objects = images;
        this.setIndex(id.toInt());
    },
    setIndex: function(idx) {
        idx = idx.toInt();
        this.current = idx;
        this.setImage(this.objects[idx].image);
    },
    _loadCallback: function() {
        this.xform = this.main = $M([
            [this.image.width,0,0],
            [0,this.image.height,0],
            [0,0,1]
        ]);
        this.render();
        this.fitToWindow();
    },
    show: function() {
        this.element.show();
        this.fireEvent('onShow', [this])
    },
    hide: function() {
        this.element.hide();
        this.fireEvent('onHide', [this])
    }
})