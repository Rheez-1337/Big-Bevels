bl_info = {
    "name": "Big Bevels",
    "author": "Rheez",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "Edit Mode: Shift+B, then 2 or 3",
    "description": "Three independent edge bevel-weight channels.",
    "category": "Mesh",
}

import bpy
import bmesh

CHANNEL_ATTRIBUTES = {
    1: "bevel_weight_edge",
    2: "bevel_weight_edge_2",
    3: "bevel_weight_edge_3",
}

addon_keymaps = []


def ensure_layer(bm, channel):
    name = CHANNEL_ATTRIBUTES[channel]
    layer = bm.edges.layers.float.get(name)
    if layer is None:
        layer = bm.edges.layers.float.new(name)
    return layer


class MESH_OT_multi_bevel_weight(bpy.types.Operator):
    bl_idname = "mesh.multi_bevel_weight"
    bl_label = "Multi Bevel Weight"
    bl_description = "Adjust one of three independent bevel-weight channels"
    bl_options = {'REGISTER', 'UNDO'}

    channel: bpy.props.IntProperty(default=1, min=1, max=3)

    def invoke(self, context, event):
        obj = context.object
        if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Multi Bevel Weight requires a mesh in Edit Mode")
            return {'CANCELLED'}

        self.start_mouse_x = event.mouse_x
        self.start_weight = 0.0

        bm = bmesh.from_edit_mesh(obj.data)
        self.layer = ensure_layer(bm, self.channel)

        self.original_values = {
            e.index: e[self.layer] for e in bm.edges if e.select
        }

        context.window_manager.modal_handler_add(self)
        self._show_status(context)
        return {'RUNNING_MODAL'}

    def _show_status(self, context):
        self.report(
            {'INFO'},
            f"Bevel Weight {self.channel}: move mouse, LMB confirm, RMB/ESC cancel"
        )

    def _switch_channel(self, bm, channel):
        self.channel = channel
        self.layer = ensure_layer(bm, channel)
        self._show_status(None)

    def modal(self, context, event):
        obj = context.object
        if not obj or obj.type != 'MESH':
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)

        # Sequential number keys select alternate channels.
        if event.type == 'TWO' and event.value == 'PRESS':
            self._switch_channel(bm, 2)
            return {'RUNNING_MODAL'}

        if event.type == 'THREE' and event.value == 'PRESS':
            self._switch_channel(bm, 3)
            return {'RUNNING_MODAL'}

        if event.type == 'ONE' and event.value == 'PRESS':
            self._switch_channel(bm, 1)
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            delta = event.mouse_x - self.start_mouse_x
            weight = max(0.0, min(1.0, self.start_weight + delta / 500.0))

            for e in bm.edges:
                if e.select:
                    e[self.layer] = weight

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"Bevel Weight {self.channel}: {weight:.3f}")
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            for e in bm.edges:
                if e.index in self.original_values:
                    e[self.layer] = self.original_values[e.index]
            bmesh.update_edit_mesh(obj.data)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


classes = (MESH_OT_multi_bevel_weight,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Mesh", space_type='EMPTY')
        kmi = km.keymap_items.new(
            "mesh.multi_bevel_weight",
            type='B',
            value='PRESS',
            shift=True,
        )
        kmi.properties.channel = 1
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
