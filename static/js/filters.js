Filters = {};
Filters.getPixels = function(img) {
    var c = this.getCanvas(img.width, img.height);
    var ctx = c.getContext('2d');
    ctx.putImageData(img, 0, 0);
    return ctx.getImageData(0,0,c.width,c.height);
};
Filters.getCanvas = function(w,h) {
    var c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
};
Filters.filterImage = function(filter, image, var_args) {
    var args = [this.getPixels(image)];
    for (var i=2; i<arguments.length; i++) {
        args.push(arguments[i]);
    }
    return filter.apply(null, args);
};
Filters.grayscale = function(pixels, args) {
    var d = pixels.data;
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        var v = 0.2126*r + 0.7152*g + 0.0722*b;
        d[i] = d[i+1] = d[i+2] = v
    }
    return pixels;
};
Filters.threshold = function(pixels, threshold, inverse) {
    var d = pixels.data;
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        var v = (0.2126*r + 0.7152*g + 0.0722*b >= threshold) ? 0 : 255;
        if (inverse) v = 255-v;
        d[i] = d[i+1] = d[i+2] = v;
    }
    return pixels;
};
Filters.threshold_average = function(pixels, inverse) {
    var d = pixels.data;
    var count = 0;
    var sum = 0;
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        var v = (0.2126*r + 0.7152*g + 0.0722*b);
        sum += v;
        count += 1;
    }
    var avg = sum/count;
    return Filters.threshold(pixels, avg, inverse);
};
Filters.histogram = function(pixels, threshold, inverse) {
    var d = pixels.data;
    var histogram = [];
    for (var i=0; i<256; i++) {
        histogram.push({count:0});
    }
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        var v = (0.2126*r + 0.7152*g + 0.0722*b >= threshold) ? 0 : 255;
        d[i] = d[i+1] = d[i+2] = v
    }
    return pixels;
};

Filters.inverse = function(pixels, args) {
    var d = pixels.data;
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        d[i] = 255 - r;
        d[i+1] = 255 - g;
        d[i+2] = 255 - b;
    }
    return pixels;
};
Filters.combine = function(pixels, pixels2) {
    var d = pixels.data;
    var d2 = pixels2.data;
    for (var i=0; i<d.length; i+=4) {
        d[i] = d[i] || d2[i];
        d[i+1] = d[i+1] || d2[i+1];
        d[i+2] = d[i+2] || d2[i+2];
        if (d[i] == 0) {
            d[i+3] = 0;
        }
    }
    return pixels;
};
Filters.floodfill = function(pixels, x, y, fillcolor, tolerance) {
    var tolerance = (!isNaN(tolerance)) ? Math.min(Math.abs(tolerance),254) : 0;
    var width = pixels.width;
    var height = pixels.height;

    var data = pixels.data;
    var length = data.length;
    var Q = [];
	var i = (x+y*width)*4;
	var e = i, w = i, me, mw, w2 = width*4;
	var targetcolor = [data[i],data[i+1],data[i+2],data[i+3]];

	if(!pixelCompare(i,targetcolor,fillcolor,data,length,tolerance)) { return pixels; }
	Q.push(i);
	while(Q.length) {
		i = Q.pop();
		if(pixelCompareAndSet(i,targetcolor,fillcolor,data,length,tolerance)) {
			e = i;
			w = i;
			mw = parseInt(i/w2)*w2; //left bound
			me = mw+w2;             //right bound
			while(mw<w && mw<(w-=4) && pixelCompareAndSet(w,targetcolor,fillcolor,data,length,tolerance)); //go left until edge hit
			while(me>e && me>(e+=4) && pixelCompareAndSet(e,targetcolor,fillcolor,data,length,tolerance)); //go right until edge hit
			for(var j=w;j<e;j+=4) {
				if(j-w2>=0      && pixelCompare(j-w2,targetcolor,fillcolor,data,length,tolerance)) Q.push(j-w2); //queue y-1
				if(j+w2<length	&& pixelCompare(j+w2,targetcolor,fillcolor,data,length,tolerance)) Q.push(j+w2); //queue y+1
			}
		}
	}
	return pixels;
}

function pixelCompare(i,targetcolor,fillcolor,data,length,tolerance) {
	if (i<0||i>=length) return false; //out of bounds
	if (data[i+3]===0 && fillcolor.a>0) return true;  //surface is invisible and fill is visible

	if (
		(targetcolor[3] === fillcolor.a) &&
		(targetcolor[0] === fillcolor.r) &&
		(targetcolor[1] === fillcolor.g) &&
		(targetcolor[2] === fillcolor.b)
	) return false; //target is same as fill

	if (
		(targetcolor[3] === data[i+3]) &&
		(targetcolor[0] === data[i]  ) &&
		(targetcolor[1] === data[i+1]) &&
		(targetcolor[2] === data[i+2])
	) return true; //target matches surface

	if (
		Math.abs(targetcolor[3] - data[i+3])<=(255-tolerance) &&
		Math.abs(targetcolor[0] - data[i]  )<=tolerance &&
		Math.abs(targetcolor[1] - data[i+1])<=tolerance &&
		Math.abs(targetcolor[2] - data[i+2])<=tolerance) return true; //target to surface within tolerance

	return false; //no match
}

function pixelCompareAndSet(i,targetcolor,fillcolor,data,length,tolerance) {
	if(pixelCompare(i,targetcolor,fillcolor,data,length,tolerance)) {
		//fill the color
		data[i]   = fillcolor.r;
		data[i+1] = fillcolor.g;
		data[i+2] = fillcolor.b;
		data[i+3] = fillcolor.a;
		return true;
	}
	return false;
}

