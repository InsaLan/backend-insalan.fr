class SeatCanvas {
  constructor(canvasElem, cellSize, pickedColor, oldSeats) {
    // parameters
    this.canvas = canvasElem;
    this.cellSize = cellSize
    this.pickedColor = pickedColor;
    this.oldSeats = oldSeats;

    // variables
    this.currentSeats = [];
    this.lastHoveredCell = null;
    this.ctx = null;

    this.isMouseDown = false;
    this.mouseDragIsPlacingSeats = false;
  }

  ////////////////////////////////////////////////// 
  // Helper functions
  ////////////////////////////////////////////////// 
  isSeat(gridX, gridY) {
    return this.currentSeats.some(seat => seat[0] === gridX && seat[1] === gridY);
  }

  removeSeat(gridX, gridY) {
    this.currentSeats = this.currentSeats.filter(seat => seat[0] !== gridX || seat[1] !== gridY);
  }

  addSeat(gridX, gridY) {
    // exclude top and left borders
    if (gridX === 0 || gridY === 0) {
      return;
    }

    if (!this.isSeat(gridX, gridY)) {
      this.currentSeats.push([gridX, gridY]);
      this.enlargeCanvasIfNecessary(gridX, gridY);
    }
  }

  initCtx() {
    this.ctx = this.canvas.getContext("2d");
    this.ctx.font = "bold 11px sans-serif";
  }

  enlargeCanvasIfNecessary(gridX, gridY) {
    let xDelta = gridX - this.canvas.width / this.cellSize + 2;
    if (xDelta > 0) {
      this.canvas.width += xDelta * this.cellSize;
    }

    let yDelta = gridY - this.canvas.height / this.cellSize + 2;
    if (yDelta > 0) {
      this.canvas.height += yDelta * this.cellSize;
    }

    // changing the canvas size resets the context, apparently
    this.initCtx();
  }

  drawText(text, x, y) {
    let textX = x * this.cellSize + 1 + this.cellSize / 8;
    let textY = y * this.cellSize + 1 + this.cellSize / 1.5;
    let maxWidth = this.cellSize - this.cellSize / 8 - 2;
    this.ctx.fillText(text, textX, textY, maxWidth)
  }

  getPickedColor() {
    return this.pickedColor
  }

  redrawCanvas() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    let largestDimension = (this.canvas.width >= this.canvas.height) ? this.canvas.width : this.canvas.height;

    const gridCount = largestDimension / this.cellSize; // number of grid cells

    this.ctx.strokeStyle = 'black'; // color of the grid lines

    // draw the grid
    for (let i = 0; i <= gridCount; i++) {
      // vertical lines
      this.ctx.beginPath();
      this.ctx.moveTo(i * this.cellSize, 0);
      this.ctx.lineTo(i * this.cellSize, this.canvas.height);
      this.ctx.stroke();

      // horizontal lines
      this.ctx.beginPath();
      this.ctx.moveTo(0, i * this.cellSize);
      this.ctx.lineTo(this.canvas.width, i * this.cellSize);
      this.ctx.stroke();
    }

    this.ctx.fillStyle = "black";
    // draw numbers on borders
    for (let x = 1; x <= gridCount; x++) {
      this.drawText(x, x, 0)
    }
    for (let y = 1; y <= gridCount; y++) {
      this.drawText(y, 0, y)
    }

    this.ctx.fillStyle = this.getPickedColor();
    for (let seat of this.currentSeats) {
      let x = seat[0];
      let y = seat[1];
      this.ctx.fillRect(x * this.cellSize + 1, y * this.cellSize + 1, this.cellSize - 2, this.cellSize - 2);
    }
  }

  ////////////////////////////////////////////////// 
  // Event handlers
  ////////////////////////////////////////////////// 
  handleMouseMove(event) {
    const bounding = this.canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / this.cellSize);
    const gridY = Math.floor(y / this.cellSize);

    // if the mouse has moved to a new cell, redraw
    if (this.lastHoveredCell === null || gridX !== this.lastHoveredCell.x || gridY !== this.lastHoveredCell.y) {
      this.lastHoveredCell = { x: gridX, y: gridY };

      if (this.isMouseDown) {
        if (this.mouseDragIsPlacingSeats) {
          this.addSeat(gridX, gridY);
        } else {
          this.removeSeat(gridX, gridY);
        }
        this.redrawCanvas();
      }
      else {
        this.redrawCanvas();

        // draw the outline on the current cell
        this.ctx.strokeStyle = 'red'; // color of the outline
        this.ctx.lineWidth = 2; // width of the outline
        this.ctx.strokeRect(gridX * this.cellSize, gridY * this.cellSize, this.cellSize, this.cellSize);
      }
    }
  }

  handleMouseDown(event) {
    this.isMouseDown = true;

    const bounding = this.canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / this.cellSize);
    const gridY = Math.floor(y / this.cellSize);

    if (this.isSeat(gridX, gridY)) {
      this.removeSeat(gridX, gridY);
      this.mouseDragIsPlacingSeats = false;
    } else {
      this.addSeat(gridX, gridY);
      this.mouseDragIsPlacingSeats = true;
    }
    this.redrawCanvas();
  }

  handleMouseUp(event) {
    this.isMouseDown = false;
  }

  ////////////////////////////////////////////////// 
  // Entry point
  ////////////////////////////////////////////////// 

  addEventListeners() {
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this))
    this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
  }

  addSeats(seats) {
    seats.forEach(seat => {
      this.currentSeats.push([seat[0], seat[1]]);
      this.enlargeCanvasIfNecessary(seat[0], seat[1]);
    });
  }

  init() {
    this.initCtx();
    this.addSeats(this.oldSeats);
    this.addEventListeners();
    this.redrawCanvas();
  }
}
