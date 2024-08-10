(function () {
  // colors for seat slots, from https://gist.github.com/bobspace/2712980
  const CSS_COLOR_NAMES = {
    Aqua: '#00FFFF',
    Aquamarine: '#7FFFD4',
    BlanchedAlmond: '#FFEBCD',
    Blue: '#0000FF',
    BlueViolet: '#8A2BE2',
    Brown: '#A52A2A',
    BurlyWood: '#DEB887',
    CadetBlue: '#5F9EA0',
    Chartreuse: '#7FFF00',
    Chocolate: '#D2691E',
    Coral: '#FF7F50',
    CornflowerBlue: '#6495ED',
    Cornsilk: '#FFF8DC',
    Crimson: '#DC143C',
    Cyan: '#00FFFF',
    DarkBlue: '#00008B',
    DarkCyan: '#008B8B',
    DarkGoldenRod: '#B8860B',
    DarkGray: '#A9A9A9',
    DarkGreen: '#006400',
    DarkKhaki: '#BDB76B',
    DarkMagenta: '#8B008B',
    DarkOliveGreen: '#556B2F',
    DarkOrange: '#FF8C00',
    DarkOrchid: '#9932CC',
    DarkRed: '#8B0000',
    DarkSalmon: '#E9967A',
    DarkSeaGreen: '#8FBC8F',
    DarkSlateBlue: '#483D8B',
    DarkSlateGray: '#2F4F4F',
    DarkTurquoise: '#00CED1',
    DarkViolet: '#9400D3',
    DeepPink: '#FF1493',
    DeepSkyBlue: '#00BFFF',
    DodgerBlue: '#1E90FF',
    FireBrick: '#B22222',
    ForestGreen: '#228B22',
    Fuchsia: '#FF00FF',
    Gold: '#FFD700',
    GoldenRod: '#DAA520',
    Gray: '#808080',
    Green: '#008000',
    GreenYellow: '#ADFF2F',
    HotPink: '#FF69B4',
    IndianRed: '#CD5C5C',
    Indigo: '#4B0082',
    Khaki: '#F0E68C',
    LawnGreen: '#7CFC00',
    LightCoral: '#F08080',
    LightGoldenRodYellow: '#FAFAD2',
    LightGreen: '#90EE90',
    LightPink: '#FFB6C1',
    LightSalmon: '#FFA07A',
    LightSeaGreen: '#20B2AA',
    LightSkyBlue: '#87CEFA',
    Lime: '#00FF00',
    LimeGreen: '#32CD32',
    Magenta: '#FF00FF',
    Maroon: '#800000',
    MediumAquaMarine: '#66CDAA',
    MediumBlue: '#0000CD',
    MediumOrchid: '#BA55D3',
    MediumPurple: '#9370DB',
    MediumSeaGreen: '#3CB371',
    MediumSlateBlue: '#7B68EE',
    MediumSpringGreen: '#00FA9A',
    MediumTurquoise: '#48D1CC',
    MediumVioletRed: '#C71585',
    MidnightBlue: '#191970',
    Navy: '#000080',
    Olive: '#808000',
    OliveDrab: '#6B8E23',
    Orange: '#FFA500',
    OrangeRed: '#FF4500',
    Orchid: '#DA70D6',
    PaleGreen: '#98FB98',
    PaleVioletRed: '#DB7093',
    Peru: '#CD853F',
    Pink: '#FFC0CB',
    Plum: '#DDA0DD',
    PowderBlue: '#B0E0E6',
    Purple: '#800080',
    RebeccaPurple: '#663399',
    Red: '#FF0000',
    RosyBrown: '#BC8F8F',
    RoyalBlue: '#4169E1',
    SaddleBrown: '#8B4513',
    Salmon: '#FA8072',
    SandyBrown: '#F4A460',
    SeaGreen: '#2E8B57',
    Sienna: '#A0522D',
    Silver: '#C0C0C0',
    SkyBlue: '#87CEEB',
    SlateBlue: '#6A5ACD',
    SlateGray: '#708090',
    SpringGreen: '#00FF7F',
    SteelBlue: '#4682B4',
    Tan: '#D2B48C',
    Teal: '#008080',
    Thistle: '#D8BFD8',
    Tomato: '#FF6347',
    Turquoise: '#40E0D0',
    Violet: '#EE82EE',
    Yellow: '#FFFF00',
    YellowGreen: '#9ACD32',
  };

  class SeatSlotCanvas extends SeatCanvas {
    constructor(canvasElem, slotSelection, cellSize, eventColor, eventSeats) {
      super(canvasElem, cellSize, eventColor, eventSeats);

      this.slotSelection = slotSelection;

      // slot id -> index in the selection widget
      this.selectionIndexes = {};

      this.currentSlot = null;
      this.slots = {};
      this.slotColors = {};
    }

    // is a seat in the given slot
    isInSeats(slotSeats, gridX, gridY) {
      return slotSeats.some(seat => seat[0] === gridX && seat[1] === gridY);
    }

    // is a seat in current slot
    isSeat(gridX, gridY) {
      let slotSeats = this.slots[this.currentSlot];
      return this.isInSeats(slotSeats, gridX, gridY);
    }

    // not used by any slot
    isFreeSeat(gridX, gridY) {
      return Object.keys(this.slots).every(slot => !this.isInSeats(this.slots[slot], gridX, gridY));
    }

    // is a seat in the event seats
    isEventSeat(gridX, gridY) {
      return super.isSeat(gridX, gridY);
    }

    addSeat(gridX, gridY) {
      if (this.currentSlot === null) {
        return;
      }

      // it's a seat, add it to the current slot
      if (this.isEventSeat(gridX, gridY) && this.isFreeSeat(gridX, gridY)) {
        this.slots[this.currentSlot].push([gridX, gridY]);
      }
    }

    removeSeat(gridX, gridY) {
      if (this.currentSlot === null) {
        return;
      }

      let slotSeats = this.slots[this.currentSlot];
      // if it's part of the current slot, remove it
      if (this.isInSeats(slotSeats, gridX, gridY)) {
        this.slots[this.currentSlot] = this.slots[this.currentSlot].filter(seat => seat[0] !== gridX || seat[1] !== gridY);
      }
    }

    getPickedColor(slot) {
      if (slot === undefined || slot === null) {
        return this.pickedColor;
      }

      if (this.slotColors[slot] === undefined) {
        // pick color not used by any slot
        let usedColors = Object.values(this.slotColors);
        let availableColors = Object.values(CSS_COLOR_NAMES).filter(color => !usedColors.includes(color));
        let pickedColor = availableColors[0];
        this.slotColors[slot] = pickedColor;
      }
      return this.slotColors[slot];
    }

    redrawSlots() {
      for (let slot of Object.keys(this.slots)) {
        this.ctx.fillStyle = this.getPickedColor(slot);
        for (let seat of this.slots[slot]) {
          let x = seat[0];
          let y = seat[1];
          this.ctx.fillRect(x * this.cellSize + 1, y * this.cellSize + 1, this.cellSize - 2, this.cellSize - 2);
        }
      }
    }

    getSlotText(slot) {
      return "Slot " + slot.toString() + " " + JSON.stringify(this.slots[slot])
    }

    createSlotOption(slot) {
      let optionElem = document.createElement("option");
      optionElem.value = slot;
      optionElem.text = this.getSlotText(slot);
      optionElem.style.color = this.getPickedColor(slot);
      return optionElem;
    }

    redrawSlotSelection() {
      for (let slot of Object.keys(this.slots)) {
        let optionElem = this.slotSelection.options[this.selectionIndexes[slot]];
        optionElem.text = this.getSlotText(slot);
      }
    }

    redrawCanvas() {
      super.redrawCanvas();
      this.redrawSlots();
      this.redrawSlotSelection();
    }

    initSlotSelection() {
      for (let [index, slot] of Object.keys(this.slots).entries()) {
        this.slotSelection.add(this.createSlotOption(slot));
        this.selectionIndexes[slot] = index;
      }
      this.slotSelection.addEventListener("change", event => {
        this.currentSlot = Number(event.target.value);
      });
    }

    handleAddSlotButton() {
      // guess an unused slot number, lol
      // django discards it later so it's fine
      let newSlot = Math.max(...Object.keys(this.slots).map(Number), 0) + 1;
      this.slots[newSlot] = [];
      this.selectionIndexes[newSlot] = this.slotSelection.options.length;
      this.slotSelection.add(this.createSlotOption(newSlot));
      this.redrawSlotSelection();
    }

    handleRemoveSlotButton() {
      let slot = this.currentSlot;
      if (slot === null) {
        return;
      }
      let idx = this.selectionIndexes[slot];
      this.slotSelection.remove(idx);
      delete this.slots[slot];
      delete this.slotColors[slot];

      // subtract 1 from indexes greater than the removed one
      for (let [slot, index] of Object.entries(this.selectionIndexes)) {
        if (index > idx) {
          this.selectionIndexes[slot] -= 1;
        }
      }

      this.currentSlot = null;
      this.redrawCanvas();
    }

    init(seatSlots) {
      super.init();
      this.slots = seatSlots;
      this.initSlotSelection();
      this.redrawSlots();

      document.getElementById("id_slot_selection_create").addEventListener("click", this.handleAddSlotButton.bind(this));
      document.getElementById("id_slot_selection_delete").addEventListener("click", this.handleRemoveSlotButton.bind(this));
    }
  }



  window.addEventListener('load', () => {
    // read parameters from the hidden input field
    let params = JSON.parse(document.getElementById("id_canvas_params").value)
    let canvas = document.getElementById("seat_canvas");

    let slotSelection = document.getElementById("id_slot_selection");

    let seatCanvas = new SeatSlotCanvas(canvas, slotSelection, params.cellSize, params.pickedColor, params.eventSeats);

    // set up form submission hook
    let seatsInput = document.getElementById("id_seat_slots");
    let form = document.getElementById("tournament_form");
    form.addEventListener("submit", event => {
      let seats = JSON.stringify(seatCanvas.slots);
      seatsInput.setAttribute("value", seats);
    });

    seatCanvas.init(params.seatSlots);
  });
})();
