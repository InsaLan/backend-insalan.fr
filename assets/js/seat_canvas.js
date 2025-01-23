class AbstractSeatCanvas {  // it's OOP-in' time
  constructor(canvasElem, cellSize) {
    // parameters
    this.canvas = canvasElem;
    this.canvas.parentElement.style.overflowX = 'scroll';
    this.cellSize = cellSize

    // variables
    this.lastHoveredCell = null;
    this.ctx = null;

    this.isMouseDown = false;
    this.mouseDragStartedOnOccupiedCell = false;
  }

  //////////////////////////////////////////////////
  // Helper functions
  //////////////////////////////////////////////////

  isOccupied(gridX, gridY) {
    // override in subclass, for all seat arrays, call isOccupiedIn
    throw new Error("isOccupied must be implemented by subclass");
  }

  isOccupiedIn(seats, gridX, gridY) {
    return seats.some(seat => seat[0] === gridX && seat[1] === gridY);
  }

  removeSeat(seats, gridX, gridY) {
    // modify in-place, cuz passed by reference
    let idx = seats.findIndex(seat => seat[0] === gridX && seat[1] === gridY);
    if (idx !== -1) {
      seats.splice(idx, 1);
    }
  }

  addSeat(seats, gridX, gridY) {
    // exclude top and left borders
    if (gridX === 0 || gridY === 0) {
      return;
    }

    if (!this.isOccupied(gridX, gridY)) {
      seats.push([gridX, gridY]);
      this.enlargeCanvasIfNecessary(gridX, gridY);
    }
  }

  initCtx() {
    this.ctx = this.canvas.getContext("2d");
    this.ctx.font = "bold 11px sans-serif";
    this.ctx.lineWidth = 2; // width of the outline
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

  //////////////////////////////////////////////////
  // Drawing functions
  //////////////////////////////////////////////////
  drawOutline(x, y) {
    this.ctx.strokeStyle = 'red'; // color of the outline
    this.ctx.strokeRect(x * this.cellSize, y * this.cellSize, this.cellSize, this.cellSize);
  }

  drawText(text, x, y) {
    let textX = x * this.cellSize + 1 + this.cellSize / 8;
    let textY = y * this.cellSize + 1 + this.cellSize / 1.5;
    let maxWidth = this.cellSize - this.cellSize / 8 - 2;
    this.ctx.fillText(text, textX, textY, maxWidth)
  }

  redrawGrid() {
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
      this.drawText(x, 0, x)
    }
  }

  redrawSeatArray(seats, color) {
    for (let [x, y] of seats) {
      this.ctx.fillStyle = color;
      this.ctx.fillRect(x * this.cellSize + 1, y * this.cellSize + 1, this.cellSize - 2, this.cellSize - 2);
    }
  }

  redrawSeats() {
    // call redrawSeatArray here
    throw new Error("redrawSeats must be implemented by subclass");
  }

  redrawCanvas() {
    this.redrawGrid();
    this.redrawSeats();
  }

  //////////////////////////////////////////////////
  // Spicy event handlers
  //////////////////////////////////////////////////

  onDragCell(event, gridX, gridY) {
    // override in subclass
  }

  onHoverCell(event, gridX, gridY) {
    // override in subclass
    this.drawOutline(gridX, gridY);
  }

  onClickCell(event, gridX, gridY) {
    // override in subclass
  }

  //////////////////////////////////////////////////
  // Basic event handlers
  //////////////////////////////////////////////////
  handleMouseMove(event) {
    const bounding = this.canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / this.cellSize);
    const gridY = Math.floor(y / this.cellSize);

    // if the mouse has moved to a new cell
    if (this.lastHoveredCell === null || gridX !== this.lastHoveredCell.x || gridY !== this.lastHoveredCell.y) {
      this.lastHoveredCell = { x: gridX, y: gridY };

      if (this.isMouseDown) {
        this.onDragCell(event, gridX, gridY);
        this.redrawCanvas();
      }
      else {
        this.redrawCanvas();
        this.onHoverCell(event, gridX, gridY);
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

    this.onClickCell(event, gridX, gridY);

    if (!this.isOccupied(gridX, gridY)) {
      this.mouseDragStartedOnOccupiedCell = false;
    } else {
      this.mouseDragStartedOnOccupiedCell = true;
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

  initSeats() {
    // override
  }

  init() {
    this.initCtx();
    this.addEventListeners();
    this.initSeats();
    this.redrawCanvas();
  }
}
