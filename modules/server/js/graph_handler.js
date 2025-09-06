class GraphHandler {
    constructor(bridge, graph,canvas)
    {
        this.graph = graph
        this.canvas = canvas
        this.bridge = bridge
    }

    connect()
    {
		this.canvas.onMouse = this.processMouseDownPre.bind(this)
        this.canvas.onMouseDown = this.processMouseDown.bind(this)
        this.canvas.onNodeMoved = this.onNodeMoved.bind(this)
		
		this.canvas.onDrawForeground = this.onDrawForeground.bind(this)
        LiteGraph.pointerListenerAdd(document,"up", this.processMouseUp.bind(this),true);
        LiteGraph.addNodeMethod("getConnectionPos",this.over_getConnectionPos)
        //LiteGraph.addNodeMethod("addInput" ,this.over_addInput)
        let that = this
        LiteGraph.addNodeMethod("onInputAdded" , function(connection) {return that.onInputAdded(this,connection)})
        LiteGraph.addNodeMethod("onOutputAdded" , function(connection) {return that.onOutputAdded(this,connection)})
        LiteGraph.addNodeMethod("rotateClockwise" , this.rotateClockwise)
        this.graph.onNodeConnectionChange = this.onNodeConnectionChange.bind(this)

        var orig = LGraphGroup.prototype.recomputeInsideNodes
        LGraphGroup.prototype.recomputeInsideNodes = function() {
            var group = this
            that.recomputeInsideNodes(group,orig)
        };
		
		this.canvas.show_info = false;
		this.canvas.onRender = this.onRender.bind(this)
		
		//this.rebindMouseEvents()
		

    }

  onInputAdded(node, connection)
  {
        let slot_pos = node.inputs.length -1
        let req = {name: connection["name"], slot: slot_pos}
        this.bridge.onGuiAction(node, "onInputAdded",req)
        return this.onSlotAdded(node,connection,LiteGraph.LEFT)
  }

  onOutputAdded(node, connection)
  {
        let slot_pos = node.outputs.length -1
        let req = {name: connection["name"], slot: slot_pos}
        this.bridge.onGuiAction(node, "onOutputAdded",req)
        return this.onSlotAdded(node,connection,LiteGraph.RIGHT)
  }

  onNodeConnectionChange(...args)
  {
     let [dir, node,slot, other_node,other_slot] = args
     let connected = !!other_node

     //workaround, recompute the output slot at disconnection
     if(LiteGraph.OUTPUT == dir && !connected)
     {
        let maxSlot = 0;
        let numElements = node.outputs.length
        for (let i = 0; i < numElements; i++) {
            let links = node.outputs[i].links
            if((!!links) && links.length > 0)
            {
                maxSlot = i + 1
            }
        }
        slot = maxSlot
     }
     let req = {output: dir == LiteGraph.OUTPUT, slot: slot, connected: connected}

    this.bridge.onGuiAction(node, "onConnectionsChange",req)

  }

  pointerUp(e)
  {
	  if (e.button >= 3)
		  return;
      if(!this.pointerStates[e.button])
        return;
	  console.log("pointer up",e.button,this.pointerStates)
	  if (e.button < 3)
	  {
		  this.pointerStates[e.button] = 0
	  }
	  this.canvas.processMouseUp(e)
	  e.preventDefault();
      e.stopPropagation();
  }
  
  pointerDown(e)
  {
	  if (e.button >= 3)
		  return;
	  console.log("pointer down",e.button)
	  if (e.button < 3)
	  {
		  this.pointerStates[e.button] = 1
	  }

	  this.canvas.processMouseDown(e)
	  e.preventDefault();
      e.stopPropagation();
  }
  
  pointerCancel(e)
  {
	  console.log("pointercancel")
  }
  
  pointerMove(e)
  {
	  if (this.pointerStates[0] != 1)
		  return;
	  console.log("pointer move")
	  this.canvas.processMouseMove(e)
	  e.preventDefault();
      e.stopPropagation();
  }

  mouseWheel(e)
  {
    this.canvas.processMouseWheel(e)
    console.log("wheel")
  }

  mouseScroll(e)
  {
    console.log("scroll")
  }

  rebindMouseEvents()
  {
		LiteGraph.pointerListenerRemove(this.canvas.canvas,"move", this.canvas._mousemove_callback,false);
		LiteGraph.pointerListenerRemove(this.canvas.canvas,"down", this.canvas._mousedown_callback,true);
		LiteGraph.pointerListenerRemove(this.canvas.canvas,"up", this.canvas._mouseup_callback,true);
		this.canvas.unbindEvents();
		this.canvas.options.skip_events = true;
		
		
		document.addEventListener("pointerup", this.pointerUp.bind(this))
		this.canvas.canvas.addEventListener("pointerup", this.pointerUp.bind(this))
		this.canvas.canvas.addEventListener("pointerdown", this.pointerDown.bind(this))
		this.canvas.canvas.addEventListener("pointercancel", this.pointerCancel.bind(this))
		document.addEventListener("pointermove", this.pointerMove.bind(this),true)
		this.canvas.canvas.addEventListener("contextmenu", (e) => e.preventDefault())
		this.canvas.canvas.addEventListener("wheel", this.mouseWheel.bind(this),true)
		this.canvas.canvas.addEventListener("scroll", this.mouseScroll.bind(this),true)
		this.pointerStates = [0,0,0]
  }

  rotateClockwise()
  {
      let node = this
      let rotation = this.node_rotation || 0
      rotation = (rotation+1) % 4
      this.horizontal = (rotation%2);
      this.flipped = rotation >= 2;
      this.node_rotation =rotation
      node.setDirtyCanvas(true,true)
  }

  onSlotAdded(node,connection, default_value)
  {
     let dir = connection.dir || default_value
        /*UP: 1,
        DOWN: 2,
        LEFT: 3,
        RIGHT: 4,
        CENTER: 5,*/
     Object.defineProperty(connection, "dir", {
                                    get: function() {
                                        let x = dir
                                        if(node.horizontal) x = [1,4,3,1,2][x]
                                        if(node.flipped) x = [4,2,1,4,3][x]
                                        return x
                                    },
                                    configurable: true,
                                    set: function(v) {
                                         dir = v
                                    },
                                });
     return connection;
  }

  over_getConnectionPos(is_input,       slot_number,        out)
  {
    let o = this._getConnectionPos(is_input,       slot_number,        out);
    if(this.flipped)
    {
        if(this.horizontal)
        {
            let h = this.flags.collapsed?0:this.size[1]
            o[1] = this.pos[1] + h - (o[1] + LiteGraph.NODE_TITLE_HEIGHT - this.pos[1])
        }
        else
        {
            let w = this.flags.collapsed?this._collapsed_width || LiteGraph.NODE_COLLAPSED_WIDTH: this.size[0]
            o[0] = this.pos[0] + w + 1 - ( o[0] - this.pos[0])
        }
    }
    return o
  }

  onRender(canvas, ctx){ // after background, before nodes
    let x = 0;
	let y = 0;
	x = x || 10;
	y = y || this.canvas.canvas.height - 80;

	ctx.save();
	ctx.translate(x, y);

	ctx.font = "10px Arial";
	ctx.fillStyle = "#888";
	ctx.textAlign = "left";
	if (this.canvas.graph) {
		ctx.fillText( "GraphLLM", 5, 13 * 0 );
		ctx.fillText( "T: " + this.graph.globaltime.toFixed(2) + "s", 5, 13 * 1 );
		ctx.fillText("I: " + this.graph.iteration, 5, 13 * 2 );
		ctx.fillText("N: " + this.graph._nodes.length + " [" + this.canvas.visible_nodes.length + "]", 5, 13 * 3 );
		ctx.fillText("V: " + this.graph._version, 5, 13 * 4);
		ctx.fillText("FPS:" + this.canvas.fps.toFixed(2), 5, 13 * 5);
	} else {
		ctx.fillText("No graph selected", 5, 13 * 1);
	}
	ctx.restore();
	
  }
  onDrawForeground(ctx, visible_rect)
  {
	 var visible_nodes = this.canvas.visible_nodes
	 var all_nodes = this.graph._nodes;
	 var hidden_nodes = all_nodes.filter((el) => !visible_nodes.includes(el));
	 hidden_nodes.map((el) => {if (el.onVisibilityChange) {
		 el.onVisibilityChange.map((f) => f(false));
		 
		 }});
	 visible_nodes.map((el) => {if (el.onVisibilityChange) {
		 el.onVisibilityChange.map((f) => f(true));
		 
		 }});
	 
  }

  onNodeMoved(node_dragged)
  {
    //console.log("dragged")
  }

  processMouseDownPre(e)
  {
	if(this.canvas.pointer_is_double) 
	{
		this.canvas.adjustMouseEvent(e);
		var mouse = [e.clientX, e.clientY];
		this.canvas.block_click = true;
		//alert("val1: " + this.canvas.last_mouse + "   val2: " + mouse) 

		this.canvas.pointer_is_double = false;
		return true;
	}
	  
  }

  processMouseDown(e)
  {
    if (this.canvas.selected_group)
    {
        if (this.canvas.selected_group.collapse_state && this.canvas.selected_group.collapse_state.is_collapsed &&this.canvas.selected_group_resizing)
        {
            this.canvas.selected_group_resizing = false
            this.canvas.selected_group.recomputeInsideNodes();
        }
    }
    if (this.canvas.node_dragged)
    {
        var draggable = true;
        for (let el in this.graph._groups)
        {
            var group = this.graph._groups[el]
            if(group.collapse_state && group.collapse_state.is_collapsed)
            {
                if(!this.canvas.node_dragged)
                {
                    console.log("strano")
                }

                var managed_nodes = Object.keys(group.collapse_state.node_info)
                if( managed_nodes.includes('' + this.canvas.node_dragged.id) )
                {
                    draggable = false
                }
            }
        }
        if(!draggable)
        {
            this.canvas.node_dragged = null
            }

    }
	
	//workaround on mobile, don't open the context menu while dragging with two fingers
	/*if(this.canvas.pointer_is_double) 
	{
		var ref_window = this.canvas.getCanvasWindow();
		LiteGraph.closeAllContextMenus(ref_window);
	}*/

  }

  groupCollapse(group)
  {
        for (var i = 0; i < group._nodes.length; ++i) {
            var node = group._nodes[i];
            var delta_pos = [ node.pos[0] - group.pos[0],  node.pos[1] - group.pos[1]]
            var new_pos = [ group.pos[0] + 20,   group.pos[1] + 70]
            group.collapse_state.node_info[node.id] = {id: node.id, size: node.size, pos: delta_pos, collapsed: node.flags.collapsed}

            node.pos = new_pos
            if(!node.flags.collapsed)
            {
                node.collapse()
            }



        }
        var internal_nodes = group._nodes.map((n) => ''+n.id)
        // remove nodes not in group
        var node_info = group.collapse_state.node_info
        node_info = Object.keys(node_info).filter((k) => internal_nodes.includes(k)).reduce((cur,key) => { return Object.assign(cur, { [key]: node_info[key] })}, {});
        group.collapse_state.node_info = node_info
        group.collapse_state.group_size = [...group.size]
        group.size = [180,110]
        group.collapse_state.color = group.color
        group.color = "#606060"
        group.collapse_state.is_collapsed = true

  }

  groupExpand(group)
  {
        group.collapse_state.is_collapsed = false
        for (var i = 0; i < group._nodes.length; ++i) {
            var node = group._nodes[i];
            var id = '' + node.id

            if(Object.keys(group.collapse_state.node_info).includes(id))
            {
                var node_info = group.collapse_state.node_info[id]
                node.pos = [group.pos[0]+node_info.pos[0], group.pos[1] + node_info.pos[1]]
                if (node.flags.collapsed && !node_info.collapsed)
                {
                    node.collapse()
                }

            }
        }
        group.size = group.collapse_state.group_size
        group.color = group.collapse_state.color

        // check overlaps with other expanded groups
        for (var i = 0; i < this.graph._groups.length; ++i) {
            var other = this.graph._groups[i]
            if(other == group)
            {
                continue;
            }
            if (!LiteGraph.overlapBounding(group._bounding, other._bounding)) {
                continue;
            }
            if (other.collapse_state && !other.collapse_state.is_collapsed)
            {
                this.groupCollapse(other)
            }
        }

  }

  processMouseUp(e)
  {

        var now = LiteGraph.getTime();
        var previousClick = this.previousClick || [0,0]
        this.previousClick = [now,this.canvas.last_mouseclick].concat( [previousClick[0], previousClick[1]])
        var total = this.previousClick[0] - this.previousClick[3]
        var t1 = (this.previousClick[0] - this.previousClick[1])
        var t2 = (this.previousClick[2] - this.previousClick[3])
        var is_double_click = (total < 300) && (t1 > 1) && (t2 > 1) && (t1 < 100) && (t2 < 100)

		var is_primary = (e.isPrimary === undefined || e.isPrimary);
        is_double_click = is_double_click && is_primary;
        var should_handle = this.canvas.selected_group && is_double_click

        if(is_double_click)
        {
            if(this.canvas.node_dragged && this.canvas.node_dragged.onDblClick)
            {
                this.canvas.node_dragged.onDblClick();
            }
        }
		
		//workaround on mobile, open the right click menu if tapping with second finger
		var is_secondary = e.isPrimary === false;
		if(is_secondary)
		{
			// is it hover a node ?
			var node = null;
			/*if (node){
				if(Object.keys(this.selected_nodes).length
				   && (this.selected_nodes[node.id] || e.shiftKey || e.ctrlKey || e.metaKey)
				){
					// is multiselected or using shift to include the now node
					if (!this.selected_nodes[node.id]) this.selectNodes([node],true); // add this if not present
				}else{
					// update selection
					this.selectNodes([node]);
				}
			}
			*/
			// show menu on this node
			this.canvas.processContextMenu(node, e);
			//alert("is secondary")
		}

        if(this.canvas.selected_group)
        {
            this.recomputeInsideNodes(this.canvas.selected_group)

        }
        if (this.canvas.align_to_grid && this.canvas.resizing_node)
        {
            this.canvas.resizing_node.size[0] = LiteGraph.CANVAS_GRID_SIZE * Math.round(this.canvas.resizing_node.size[0] / LiteGraph.CANVAS_GRID_SIZE);
            this.canvas.resizing_node.size[1] = LiteGraph.CANVAS_GRID_SIZE * Math.round(this.canvas.resizing_node.size[1] / LiteGraph.CANVAS_GRID_SIZE);
        }

        if(this.canvas.node_dragged || this.canvas.resizing_node)
        {
            let node = this.canvas.node_dragged || this.canvas.resizing_node
            this.recomputeOutsideGroup(node)

            if (node.constructor.name == "GroupNodeGui")
            {
                node.recomputeInsideNodes()
            }
        }

        if(should_handle)
        {
            var group = this.canvas.selected_group
            if (group.collapse_state === undefined)
            {
                group.collapse_state = { is_collapsed: false, node_info: new Object()}
            }
            if (group.collapse_state.is_collapsed)
            {
                this.groupExpand(group)
                //
            }
            else
            {
                this.groupCollapse(group)

            }
        }
        //console.log("group: " + this.canvas.selected_group + "   double " + is_double_click + "   time: "
        //+ (now - this.canvas.last_mouseclick), " p " + this.previousClick + "  t " + [total,t1,t2])

    return false;
  }

   recomputeOutsideGroup(node)
  {
    var node_bounding = new Float32Array(4);
    node.getBounding(node_bounding);

    if (node.parent_group)
    {
        if (LiteGraph.overlapBounding(node.parent_group._bounding, node_bounding)) {
            return;
        }

    }

    var found_group = null
    for (var i = 0; i < this.graph._groups.length; ++i) {
        var group = this.graph._groups[i]
        if (!LiteGraph.overlapBounding(group._bounding, node_bounding)) {
            continue;
        }
        found_group = group
    }

    if (node.constructor.name != "GroupNodeGui")
    {
        for (var i = 0; i < this.graph._nodes.length; ++i) {
            var group = this.graph._nodes[i];
            if(group == node)
            {
                continue;
            }
            if (group.constructor.name != "GroupNodeGui")
            {
                continue
            }
            if (!LiteGraph.overlapBounding(group._bounding, node_bounding)) {
                continue;
            }
            if (group.flags.collapsed)
            {
                continue
            }
            found_group = group
        }
    }

    if (found_group)
    {
        if(node.parent_group && node.parent_group._nodes)
        {
            deleteByValue(node.parent_group._nodes, node)
        }
        if(found_group._nodes)
        {
            deleteByValue(found_group._nodes, node)
            found_group._nodes.push(node)
        }



        node.parent_group = found_group

        function deleteByValue(obj, val) {
            var index = obj.indexOf(val);
            if (index !== -1) {
              obj.splice(index, 1);
            }
        }




    }
    else
    {
        node.parent_group = null
    }

  }

  recomputeInsideNodes(group, orig)
  {
    group._nodes.length = 0;
    var nodes = this.graph._nodes;
    var node_bounding = new Float32Array(4);

    for (var i = 0; i < nodes.length; ++i) {
        var node = nodes[i];
        node.getBounding(node_bounding);
        if(node == group)
        {
            continue;
        }
        if (group.constructor.name == "GroupNodeGui" && node.constructor.name == "GroupNodeGui")
        {
            continue;
        }

        if (!LiteGraph.overlapBounding(group._bounding, node_bounding)) {
            continue;
        } //out of the visible area
        if(node.parent_group && node.parent_group != group)
        {
            var parent_group = node.parent_group
            if (group.constructor.name == "GroupNodeGui" && node.parent_group.constructor.name != "GroupNodeGui")
            {

                console.log("stealing")
            }
            else
            {
                if (LiteGraph.overlapBounding(parent_group._bounding, node_bounding)) {
                continue;
                }
            }


        }
        group._nodes.push(node);
        node.parent_group = group
    }

  }
}