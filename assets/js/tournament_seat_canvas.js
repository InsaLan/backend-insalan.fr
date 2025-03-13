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

  class SlotSelection {
    constructor(selectElem, errorElem, params) {
      this.selectElem = selectElem;
      this.errorElem = errorElem;

      // slot id -> index in the selection widget
      this.selectionIndexes = {};
      this.slotColors = {};

      this.slots = params.seatSlots;
      this.seatsPerSlot = params.seatsPerSlot;
    }

    getSlotColor(slot) {
      if (slot === undefined || slot === null) {
        throw new Error("slot is required");
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


    initSlotSelection() {
      for (let [index, slot] of Object.keys(this.slots).entries()) {
        this.selectElem.add(this.createSlotOption(slot));
        this.selectionIndexes[slot] = index;
      }
    }

    getSlotText(slot) {
      return "Slot " + slot.toString() + " " + JSON.stringify(this.slots[slot])
    }

    createSlotOption(slot) {
      let optionElem = document.createElement("option");
      optionElem.value = slot;
      optionElem.text = this.getSlotText(slot);
      return optionElem;
    }

    redrawColoredBlock(optionElem, color) {
      // apparently this *NEEDS* to be done each draw.
      // cursed but it works
      let div = document.createElement("span");
      div.style.display = "inline-block";
      div.textContent = "██";
      div.style.color = color;
      optionElem.insertBefore(div, optionElem.firstChild);
    }

    redrawSlotSelection() {
      for (let slot of Object.keys(this.slots)) {
        let optionElem = this.selectElem.options[this.selectionIndexes[slot]];
        optionElem.text = this.getSlotText(slot);
        this.redrawColoredBlock(optionElem, this.getSlotColor(slot));
      }
      this.validateSlots();
    }

    validateSlots() {
      let errors = [];
      for (let slot of Object.keys(this.slots)) {
        if (this.slots[slot].length !== this.seatsPerSlot) {
          errors.push("Slot " + slot.toString() + " has " + this.slots[slot].length + " seats, expected " + this.seatsPerSlot);
        }
      }
      if (errors.length > 0) {
        this.errorElem.textContent = errors.join("\r\n");
      } else {
        this.errorElem.textContent = "";
      }
    }

    triggerEvent(eventType, slot) {
      let event = new Event(eventType);
      event.slot = slot;
      this.selectElem.dispatchEvent(event);
    }

    handleAddSlotButton() {
      // guess an unused slot number, lol
      // django discards it later so it's fine
      let newSlot = Math.max(...Object.keys(this.slots).map(Number), 0) + 1;
      this.selectionIndexes[newSlot] = this.selectElem.options.length;
      this.slots[newSlot] = [];
      this.selectElem.add(this.createSlotOption(newSlot));
      this.redrawSlotSelection();
      this.selectElem.value = newSlot;
      this.triggerEvent("select", newSlot);
    }

    handleRemoveSlotButton() {
      let slot = this.selectElem.value;
      if (slot === null || slot === "" || slot === undefined) {
        return;
      }
      let idx = this.selectionIndexes[slot];
      this.selectElem.remove(idx);
      delete this.slots[slot];
      delete this.slotColors[slot];

      // subtract 1 from indexes greater than the removed one
      for (let [slot, index] of Object.entries(this.selectionIndexes)) {
        if (index > idx) {
          this.selectionIndexes[slot] -= 1;
        }
      }
      delete this.selectionIndexes[slot];

      let prevSlot = Object.keys(this.slots).find(slot => this.selectionIndexes[slot] === idx - 1);
      this.selectElem.value = prevSlot;
      this.triggerEvent("select", prevSlot);
    }

    addEventListeners() {
      document.getElementById("id_slot_selection_create").addEventListener("click", this.handleAddSlotButton.bind(this));
      document.getElementById("id_slot_selection_delete").addEventListener("click", this.handleRemoveSlotButton.bind(this));
      this.selectElem.addEventListener("change", event => {
        this.triggerEvent("select", Number(event.target.value));
      });
    }
  }

  class SeatSlotCanvas extends AbstractSeatCanvas {
    constructor(canvasElem, slotSelection, params) {
      super(canvasElem, params.cellSize);

      this.slotSelection = slotSelection;

      this.eventSeatColor = params.pickedColor;
      this.eventSeats = params.eventSeats;
      this.unavailableSeats = params.unavailableSeats;  // seats used by other tournaments in same event

      this.currentSlot = null;
    }

    isOccupied(gridX, gridY) {
      // must be in event seats
      if (!this.isOccupiedIn(this.eventSeats, gridX, gridY)) {
        return true;
      }

      // check unavailable seats
      if (this.isOccupiedIn(this.unavailableSeats, gridX, gridY)) {
        return true;
      }

      // check all slots
      for (let seats of Object.values(this.slotSelection.slots)) {
        if (this.isOccupiedIn(seats, gridX, gridY)) {
          return true;
        }
      }

      return false;
    }

    onDragCell(event, gridX, gridY) {
      if (this.currentSlot === null) {
        return;
      }
      let seats = this.slotSelection.slots[this.currentSlot]

      if (this.mouseDragStartedOnOccupiedCell) {
        if (!this.isOccupied(gridX, gridY)) {
          this.addSeat(seats, gridX, gridY);
        }
      } else {
        if (this.isOccupiedIn(seats, gridX, gridY)) {
          this.removeSeat(seats, gridX, gridY);
        }
      }
    }

    onClickCell(event, gridX, gridY) {
      if (this.currentSlot === null) {
        return;
      }
      let seats = this.slotSelection.slots[this.currentSlot]

      if (this.isOccupiedIn(seats, gridX, gridY)) {
        this.removeSeat(seats, gridX, gridY);
      } else if (!this.isOccupied(gridX, gridY)) {
        this.addSeat(seats, gridX, gridY);
      }
    }

    redrawSeats() {
      this.redrawSeatArray(this.eventSeats, this.eventSeatColor);
      this.redrawSeatArray(this.unavailableSeats, "black");

      for (let [slot, seats] of Object.entries(this.slotSelection.slots)) {
        this.redrawSeatArray(seats, this.slotSelection.getSlotColor(slot));
      }
    }

    initSeats() {
      let maxX = Math.max(...this.eventSeats.map(seat => seat[0]), 0);
      let maxY = Math.max(...this.eventSeats.map(seat => seat[1]), 0);
      this.enlargeCanvasIfNecessary(maxX, maxY);

      this.slotSelection.initSlotSelection();
    }

    redrawCanvas() {
      super.redrawCanvas();
      this.slotSelection.redrawSlotSelection();
    }

    addEventListeners() {
      super.addEventListeners();
      this.slotSelection.addEventListeners();
      this.slotSelection.selectElem.addEventListener("select", event => {
        this.currentSlot = event.slot;
        this.redrawCanvas();
      });
    }
  }

  window.addEventListener('load', () => {
    // read parameters from the hidden input field
    let params = JSON.parse(document.getElementById("id_canvas_params").value)
    let canvas = document.getElementById("seat_canvas");

    let selectElem = document.getElementById("id_slot_selection");
    let errorElem = document.getElementById("id_slot_selection_error");

    let slotSelection = new SlotSelection(selectElem, errorElem, params);
    let seatCanvas = new SeatSlotCanvas(canvas, slotSelection, params);

    // set up form submission hook
    let seatsInput = document.getElementById("id_seat_slots");
    let form = document.getElementById("eventtournament_form");
    form.addEventListener("submit", event => {
      let seats = JSON.stringify(slotSelection.slots);
      seatsInput.setAttribute("value", seats);
    });

    seatCanvas.init();
  });
})();
