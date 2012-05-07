

Frog.Viewer = new Class({
    Implements: Events,
    initialize: function() {
        this.origin = {x: 0, y: 0};
        this.xform = Matrix.I(3);
        this.main = Matrix.I(3);
        this.scaleValue = 1.0;
        //this.trans = Matrix.I(3);
        //this.scale = Matrix.I(3);

        this.items = [];
        this.current = 0;
        this.isMouseDown = false;

        this.element = new Element('div', {id: 'frog_viewer'}).inject(document.body);
        this.canvas = new Element('canvas', {width: window.getWidth(), height: window.getHeight()}).inject(this.element);

        this.ctx = this.canvas.getContext('2d');
        this.image = new Image();
        this.image.onload = this.render.bind(this);

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
        this.setImage("/static/28/1000000000000028/3b15be84aff20b322a93c0b9aaa62e25ad33b4b4.jpg");
    },
    toElement: function() {
        return this.element;
    },
    up: function(e) {
        this.isMouseDown = false;
        this.main = this.xform;
    },
    down: function(e) {
        this.isMouseDown = true;
        this.origin.x = e.client.x;
        this.origin.y = e.client.y;
    },
    move: function(e) {
        if (this.isMouseDown) {
            var x = e.client.x - this.origin.x;
            var y = e.client.y - this.origin.y;
            
            //this.xform.elements[2][0] = this.origin.elements[2][0] * 1 + this.origin.elements[2][1] * 0 + x;

            this.xform = Matrix.I(3).x(this.main);
            // this.translate(e.client.x, e.client.y);
            // this.translate(this.origin.x, this.origin.y)
            this.translate(x,y);
            //console.log(this.xform.elements[2][0], this.xform.elements[2][1])
            // this.translate(x+this.origin.x,y+this.origin.y);

            //this.xform = m.dup();
            this.render();
        }
    },
    zoom: function(e) {
        e.stop();
        //var iRatio = this.main.elements[0][0] / this.main.elements[1][1];
        if (e.wheel > 0) {
            this.scaleValue += 0.05;
        }
        else {
            this.scaleValue -= 0.05;
        }
        this.scaleValue = (this.scaleValue > 2.0) ? 2.0 : this.scaleValue;
        this.scaleValue = (this.scaleValue < 0.3) ? 0.3 : this.scaleValue;
        // this.origin.x = e.client.x;
        // this.origin.y = e.client.y;
        this.main = Matrix.I(3);
        var x = e.client.x - this.main.elements[2][0];
        var y = e.client.y - this.main.elements[2][1];
        var x1 = this.origin.x - e.client.x;
        var y1 = this.origin.y - e.client.y;
        this.xform = Matrix.I(3)//.x(this.main);
        this.translate(-e.client.x.toFloat(), -e.client.y.toFloat());
        // this.translate(x, y);
        this.scale(-this.scaleValue, -this.scaleValue);
        // this.translate(e.client.x.toFloat(), e.client.y.toFloat());
        this.translate(-200,-200);
        // this.translate(x, y);
        // this.translate(x1, y1);
        this.main = this.xform;
        this.render();
    },
    clear: function() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    },
    render: function() {
        this.clear();
        //var x = this.origin.x * this.xform.elements[0][0] + this.origin.y * this.xform.elements[1][0] + this.xform.elements[2][0];
        //var y = this.origin.x * this.xform.elements[0][1] + this.origin.y * this.xform.elements[1][1] + this.xform.elements[2][1];
        
        this.ctx.drawImage(
            this.image, 
            this.xform.elements[2][0],
            this.xform.elements[2][1],
            this.image.width * this.scaleValue, 
            this.image.height * this.scaleValue);
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
        this.image.src = img;
    }
})