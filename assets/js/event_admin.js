(function () {
  // parameters
  let cellSize;
  let pickedColor;

  // variables
  let currentSeats = [];
  let lastHoveredCell = null;
  let canvas;
  let ctx;

  let isMouseDown = false;
  let mouseDragIsPlacingSeats = false;

  ////////////////////////////////////////////////// 
  // Helper functions
  ////////////////////////////////////////////////// 

  function isSeat(gridX, gridY) {
    return currentSeats.some(seat => seat[0] === gridX && seat[1] === gridY);
  }

  function removeSeat(gridX, gridY) {
    currentSeats = currentSeats.filter(seat => seat[0] !== gridX || seat[1] !== gridY);
  }

  function addSeat(gridX, gridY) {
    if (!isSeat(gridX, gridY)) {
      currentSeats.push([gridX, gridY]);
      enlargeCanvasIfNecessary(gridX, gridY);
    }
  }

  function enlargeCanvasIfNecessary(gridX, gridY) {
    let xDelta = gridX - canvas.width / cellSize + 2;
    if (xDelta > 0) {
      canvas.width += xDelta * cellSize;
    }

    let yDelta = gridY - canvas.height / cellSize + 2;
    if (yDelta > 0) {
      canvas.height += yDelta * cellSize;
    }
  }

  function redrawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const gridCount = canvas.width / cellSize; // number of grid cells

    ctx.strokeStyle = 'black'; // color of the grid lines

    // draw the grid
    for (let i = 0; i <= gridCount; i++) {
      // vertical lines
      ctx.beginPath();
      ctx.moveTo(i * cellSize, 0);
      ctx.lineTo(i * cellSize, canvas.height);
      ctx.stroke();

      // horizontal lines
      ctx.beginPath();
      ctx.moveTo(0, i * cellSize);
      ctx.lineTo(canvas.width, i * cellSize);
      ctx.stroke();
    }
    ctx.fillStyle = pickedColor;
    for (let seat of currentSeats) {
      let x = seat[0];
      let y = seat[1];
      ctx.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, cellSize - 2);
    }
  }

  ////////////////////////////////////////////////// 
  // Event handlers
  ////////////////////////////////////////////////// 

  function handleMouseMove(event) {
    const bounding = canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / cellSize);
    const gridY = Math.floor(y / cellSize);

    // if the mouse has moved to a new cell, redraw
    if (lastHoveredCell === null || gridX !== lastHoveredCell.x || gridY !== lastHoveredCell.y) {
      lastHoveredCell = { x: gridX, y: gridY };

      if (isMouseDown) {
        if (mouseDragIsPlacingSeats) {
          addSeat(gridX, gridY);
        } else {
          removeSeat(gridX, gridY);
        }
        redrawCanvas();
      }
      else {
        redrawCanvas();

        // draw the outline on the current cell
        ctx.strokeStyle = 'red'; // color of the outline
        ctx.lineWidth = 2; // width of the outline
        ctx.strokeRect(gridX * cellSize, gridY * cellSize, cellSize, cellSize);
      }

    }
  }

  function handleMouseDown(event) {
    isMouseDown = true;

    const bounding = canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / cellSize);
    const gridY = Math.floor(y / cellSize);

    if (isSeat(gridX, gridY)) {
      removeSeat(gridX, gridY);
      mouseDragIsPlacingSeats = false;
    } else {
      addSeat(gridX, gridY);
      mouseDragIsPlacingSeats = true;
    }
    redrawCanvas();
  }

  function handleMouseUp(event) {
    isMouseDown = false;
  }

  ////////////////////////////////////////////////// 
  // Entry point
  ////////////////////////////////////////////////// 

  window.onload = function () {
    // get the canvas and context
    canvas = document.getElementById("seat_canvas");
    ctx = canvas.getContext("2d");

    // set up form submission hook
    let seats_input = document.getElementById("id_seats");
    document.getElementById("event_form").addEventListener("submit", event => {
      pixels = JSON.stringify(currentSeats);
      seats_input.setAttribute("value", pixels);
    });

    // get params from the hidden input
    let params = JSON.parse(document.getElementById("id_canvas_params").value)
    cellSize = params.cellSize;
    pickedColor = params.pickedColor;

    // draw old seats
    params.oldSeats.forEach(seat => {
      addSeat(seat[0], seat[1]);
    });

    // main
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mousedown', handleMouseDown)
    canvas.addEventListener('mouseup', handleMouseUp);

    redrawCanvas();

  }
})();
