function computePixelValue(dimension, value, parent) {
  
    let pixelValue = null;
      
    if (!value) return null;
    
    if (value.endsWith('vw') && dimension === 'width') {
        const vw = parseFloat(value);
        pixelValue = (vw / 100) * window.innerWidth;
    
    } else if (value.endsWith('vh') && dimension === 'height') {
        const vh = parseFloat(value);
        pixelValue = (vh / 100) * window.innerHeight;
    
    } else if (value.endsWith('px')) {
        pixelValue = parseFloat(value);
    
    } else if (value.endsWith('%')) {
        const percent = parseFloat(value);

        if (parent) {
            const parentRect = parent.getBoundingClientRect();
            pixelValue = (percent / 100) 
            pixelValue *= dimension === 'width' ? parentRect.width : parentRect.height;
            if (pixelValue < 0 || pixelValue === 0) {
                console.warn('Computed pixel value is zero or negative. Using default.');
                pixelValue = dimension === 'width' ? 1200 : 800; // Default values
            } 
        } else {
            console.warn('Parent element is not provided for percentage calculation. Using default 100% of the viewport.');
            pixelValue = (percent / 100) * (dimension === 'width' ? window.innerWidth : window.innerHeight);
        }
    } 

    return pixelValue;
}