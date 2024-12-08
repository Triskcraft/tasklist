from mcdreforged.api.all import *
import json
import os
import re

Prefix = "!!task"
list_main = []
list_generic = []
TASK_FILE = "task.json"

def on_load(server: PluginServerInterface, info):
    global list_main, list_generic
    tasks = load_tasks()
    list_main = tasks['main']
    list_generic = tasks['generic']
    server.register_help_message(Prefix, "Mensaje de ayuda para la lista de tareas")
    server.register_command(
        Literal(Prefix).runs(lambda src: display_msg(src))
        .then(Literal('help').runs(lambda src: display_msg(src)))
        .then(Literal('add')
            .then(Literal('main')
                .then(Text('task_name')
                    .then(GreedyText('task_details').runs(lambda src, ctx: add_task(src, server, list_main, ctx['task_name'], ctx['task_details']))
                    )
                )
            )
            .then(Literal('generic')
                .then(Text('task_name')
                    .then(GreedyText('task_details').runs(lambda src, ctx: add_task(src, server, list_generic, ctx['task_name'], ctx['task_details']))
                    )
                )
            )
        )
        .then(Literal('list').runs(lambda src: display_list(src, None))
            .then(Literal('main').runs(lambda src: display_list(src, 'main')))
            .then(Literal('generic').runs(lambda src: display_list(src, 'generic')))
        )
        .then(Literal('delete')
            .then(Text('task_name').runs(lambda src, ctx: delete_task(src, ctx['task_name'])))
        )
        .then(Literal('delete_comment')
            .then(Text('task_name')
                .then(Text('comment_index').runs(lambda src, ctx: delete_comment(src, ctx['task_name'], int(ctx['comment_index']))))
            )
        )
        .then(Literal('modify')
            .then(Text('task_name')
                .then(Literal('user')
                    .then(Text('player').runs(lambda src, ctx: modify_task(src, server, 'user', ctx['task_name'], ctx['player'])))
                )
                .then(Literal('coords')
                    .then(Literal('here').runs(lambda src, ctx: modify_task(src, server, 'coords', ctx['task_name'], 'here')))
                    .then(Integer('x')
                        .then(Integer('y')
                            .then(Integer('z').runs(lambda src, ctx: modify_task(src, server, 'coords', ctx['task_name'], [ctx['x'], ctx['y'], ctx['z']]))
                            )
                        )
                    )
                )
                .then(Literal('details')
                    .then(GreedyText('descripcion').runs(lambda src, ctx: modify_task(src, server, 'details', ctx['task_name'], ctx['descripcion'])))
                )
                .then(Literal('comment')
                    .then(GreedyText('comentario').runs(lambda src, ctx: modify_task(src, server, 'comment', ctx['task_name'], ctx['comentario'])))
                )
            )
        )
        .then(Literal('view')
            .then(Text('task_name').runs(lambda src, ctx: view_task(src, ctx['task_name']))
            )
        )
    )
    
def display_msg(src: CommandSource):
    src.reply("§6Comandos de Tareas:\n"+
        "§e!!task help §7- comando de ayuda\n"+
        "§e!!task add §a(main/generic) §b<nombre> <detalles> §7- Añadir una nueva tarea a la lista.\n"+
        "§e!!task list §7- Ver la lista de tareas.\n"+
        "§e!!task delete §b<nombre> §7- Borrar una tarea.\n"+
        "§e!!task delete_comment §b<nombre> <id> §7- Borrar un comentario.\n"+
        "§e!!task view §b<nombre> §7- Ver la lista de comentarios.\n"+
        "§e!!task modify §b<nombre> §acoords here §7- actualizar las coordenadas a tu pocicion actual\n"+
        "§e!!task modify §b<nombre> §a(user/coords/details/comment) §b<datos> §7- Añadir o modificar datos de una tarea. §o(Los comentarios no se reemplazan al añadir uno nuevo.)"
    )

def display_list(src: CommandSource, list_name=None):
    tasks = dict([('main', list_main), ('generic', list_generic)])
    
    
    if list_name is None:
        src.reply("§6§lLista de tareas: §emain §7y §egeneric§7.\n")
        for list_name, task_list in tasks.items():
            task_button = RText(" §e[+]").set_hover_text("Agregar nueva tarea").set_click_event(
                RAction.suggest_command, f"{Prefix} add {list_name} ")
            src.reply(RTextList(f"§e§l{list_name}",task_button," §e§l:\n"))
            show_task_list(src, task_list)
            src.reply("\n")
    elif list_name in tasks:
        src.reply(f"§6§lLista de tareas: §e{list_name}§7.\n")
        show_task_list(src, tasks[list_name])
    else:
        src.reply("§cLista de tareas no encontrada. Usa §emainc7 o §egeneric§7.")

def show_task_list(src: CommandSource, task_list):
    if not task_list:
        src.reply("§cNo hay tareas en esta lista.")
    else:
        for task in task_list:
            if task["coords"]["dim"] == 'overworld':
                coords_color = 'a'
            elif task["coords"]["dim"] == 'the_nether':
                coords_color = 'c'
            elif task["coords"]["dim"] == 'the_end':
                coords_color = 'd'  
            else:
                coords_color = 'f'
                
            task_text = RText(f"§a- {task['name']} ").set_hover_text(
                f"§6Tarea: §b{task['name']}\n" +
                f"§7Coordenadas: §{coords_color}{task['coords']['x']}, {task['coords']['y']}, {task['coords']['z']}\n" +
                f"§7Descripción: §e{task['details']}\n" +
                f"§7Encargado: §b{task['user']}"
            ).set_click_event(RAction.suggest_command, f"{Prefix} view {task['name']}")

            add_button = RText(" §a[+]§7").set_hover_text("Agregar sub-tarea").set_click_event(
                RAction.suggest_command, f"{Prefix} modify {task['name']} comment ")
            delete_button = RText(" §c[-]§7").set_hover_text("Eliminar tarea").set_click_event(
                RAction.suggest_command, f"{Prefix} delete {task['name']} ")
            tp_button = RText(" §9[tp]").set_hover_text("tp a coordenadas del proyecto").set_click_event(
                RAction.run_command, f"/tp {task['coords']['x']} {task['coords']['y']} {task['coords']['z']}")
            waypoint_button = RText(' §b[+v]').set_hover_text('§bCtrl + clic para añadir waypoint').set_click_event(
			    RAction.run_command, f"/newWaypoint x:{task['coords']['x']}, y:{task['coords']['y']}, z:{task['coords']['z']}, dim:{task['coords']['dim']}")


            src.reply(RTextList(task_text, add_button, delete_button, waypoint_button))

def get_coords(src: CommandSource, server: PluginServerInterface):
    player = src.player
    coordsstr = re.search(r'\[([^\]]+)\]', server.rcon_query('data get entity {} Pos'.format(player)))
    dim = re.search(r'"minecraft:([^"]+)"',server.rcon_query('data get entity {} Dimension'.format(player))).group(1)
    print(dim)
    coords = [int(float(num)) for num in re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', coordsstr.group(1))]
    return({'x': coords[0],'y': coords[1],'z': coords[2], 'dim': dim})

def add_task(src: CommandSource, server: PluginServerInterface, list, task_name, task_details):
    player = src.player
    coords = get_coords(src, server)

    list.append({'name': task_name, 'details': task_details, 'user': player, 'coords': coords,'comment':[]})
    src.reply(f"§aTarea {task_name} Agregada Correctamente.")
    save_tasks({'main': list_main, 'generic': list_generic})

def modify_task(src: CommandSource, server: PluginServerInterface, attribute, task_name, data):
    tasks = [('main', list_main), ('generic', list_generic)]

    for list_name, task_list in tasks:
        for task in task_list:
            if task['name'] == task_name:
                if attribute == 'comment':
                    task['comment'].append(data)
                    src.reply(f"§aNuevo comentario agregado a la tarea {task_name}")
                    save_tasks({'main': list_main, 'generic': list_generic})
                    return
                elif attribute == 'coords':
                    if data == 'here':
                        data = get_coords(src, server)
                        task['coords'] = data
                        src.reply(f"§aTarea {task_name} actualizada a coordenadas x:{task['coords']['x']}, y:{task['coords']['y']}, z:{task['coords']['z']}")
                        save_tasks({'main': list_main, 'generic': list_generic})
                        return
                    else:
                        task['coords']['x'] = data[0]
                        task['coords']['y'] = data[1]
                        task['coords']['z'] = data[2]
                        src.reply(f"§aTarea {task_name} actualizada a coordenadas x:{task['coords']['x']}, y:{task['coords']['y']}, z:{task['coords']['z']}")
                        save_tasks({'main': list_main, 'generic': list_generic})
                        return
                else:
                    task[attribute] = data
                    src.reply(f"§aTarea {task_name} modificada: {attribute} actualizado a {data}")
                    save_tasks({'main': list_main, 'generic': list_generic})
                    return

    src.reply(f"Tarea {task_name} no encontrada en ninguna lista.")

def view_task(src: CommandSource, task_name): 
    tasks = [('main', list_main), ('generic', list_generic)]

    for list_name, task_list in tasks:
        for task in task_list:
            if task['name'] == task_name:
                if 'comment' in task:
                    if task["coords"]["dim"] == 'overworld':
                        coords_color = 'a'
                    elif task["coords"]["dim"] == 'the_nether':
                        coords_color = 'c'
                    elif task["coords"]["dim"] == 'the_end':
                        coords_color = 'd'  
                    else:
                        coords_color = 'f'
                    waypoint_button = RText(' §b[+v]').set_hover_text('§bCtrl + clic para añadir waypoint').set_click_event(
			            RAction.run_command, f"/newWaypoint x:{task['coords']['x']}, y:{task['coords']['y']}, z:{task['coords']['z']}, dim:{task['coords']['dim']} ")
                    delete_button = RText(" §c[-]§7").set_hover_text("Eliminar tarea").set_click_event(
                        RAction.suggest_command, f"{Prefix} delete {task['name']} ")
                    add_button = RText(" §a[+]§7").set_hover_text("Agregar sub-tarea").set_click_event(
                        RAction.suggest_command, f"{Prefix} modify {task['name']} comment ")

                    comments = task['comment']
                    src.reply(f"§6§lComentarios para la tarea §b{task_name}"+
                              add_button + delete_button + waypoint_button + 
                              f"\n§7Descripción: §e{task['details']}\n"+
                              f"§7Encargado: §b{task['user']} §7coords: §{coords_color}x: {task['coords']['x']}, y:{task['coords']['y']}, z:{task['coords']['z']}")
                    for idx, comment in enumerate(comments, start=1):
                        delete_command = f"{Prefix} delete_comment {task_name} {idx - 1}"
                        delete_button = RText(" §c[-]§7").set_hover_text("Eliminar comentario").set_click_event(RAction.suggest_command, delete_command)

                        src.reply(RTextList(RText(f"§e- {comment} "), delete_button))
                else:
                    src.reply(f"§eLa tarea §b{task_name} §eno tiene comentarios.")
                return
    src.reply(f"Tarea {task_name} no encontrada.")

def delete_task(src: CommandSource, task_name):
    tasks = [('main', list_main), ('generic', list_generic)]
    
    for list_name, task_list in tasks:
        for task in task_list:
            if task['name'] == task_name:
                task_list.remove(task)
                src.reply(f"§cTarea §b{task_name}§c eliminada.")
                save_tasks({'main': list_main, 'generic': list_generic})
                return
    
    src.reply(f"Tarea {task_name} no encontrada.")

def delete_comment(src: CommandSource, task_name, comment_index):
    tasks = [('main', list_main), ('generic', list_generic)]
    
    for list_name, task_list in tasks:
        for task in task_list:
            if task['name'] == task_name:
                if 'comment' in task and isinstance(task['comment'], list):
                    try:
                        deleted_comment = task['comment'].pop(comment_index)
                        src.reply(f"§cComentario eliminado: {deleted_comment}")
                    except IndexError:
                        src.reply(f"No se pudo eliminar el comentario en la posición {comment_index - 1}")
                else:
                    src.reply(f"§cLa tarea §b{task_name}§c no tiene comentarios")
                return
    
    src.reply(f"Tarea {task_name} no encontrada.")

def save_tasks(tasks):
    with open(TASK_FILE, 'w') as file:
        json.dump(tasks, file, indent=4)

def load_tasks():
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {'main': [], 'generic': []}
    else:
        return {'main': [], 'generic': []}
