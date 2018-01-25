import hlt
import logging 
from collections import OrderedDict
import math

game = hlt.Game('Sond-v7')
logging.info('Starting...')

docked_planets = {}
starting_ship_ids = {}
committed_ships = {}

round_counter = -1
twos = 0
init = True
twos_aggro_init = 0
start_twos_aggro = 0

###############################################################################

def escape(self,target,distance_to_nearest_enemy, min_distance = 25):
    logging.info('Distance to nearest {}'.format(distance_to_nearest_enemy))
    if int(distance_to_nearest_enemy) > 30:
        logging.info('Going corner')
        top_left_distance = hlt.entity.Entity.calculate_distance_between(ship, hlt.entity.Position(0,0))
        top_right_distance = hlt.entity.Entity.calculate_distance_between(ship, hlt.entity.Position(240,0))
        bottom_left_distance = hlt.entity.Entity.calculate_distance_between(ship, hlt.entity.Position(0,160))
        bottom_right_distance = hlt.entity.Entity.calculate_distance_between(ship, hlt.entity.Position(240,160))
        _min = min(top_left_distance,top_right_distance,bottom_left_distance,bottom_right_distance)        
        if top_left_distance == _min: return hlt.entity.Position(3,3)
        if top_right_distance == _min: return hlt.entity.Position(237,3)
        if bottom_left_distance == _min: return hlt.entity.Position(3,157)
        if bottom_right_distance == _min: return hlt.entity.Position(237,157)        
        else: logging.info('ESCAPE ERROR')
    else:
        logging.info('Going circular')
        angle = target.calculate_angle_between(self)
        radius = target.radius + min_distance
        x = target.x + radius * math.cos(math.radians(angle))
        y = target.y + radius * math.sin(math.radians(angle))
        logging.info('Position: {}\nx: {}\ny: {}'.format(hlt.entity.Position(x,y), x, y))
        if x < 10 or x > 230 or y < 10 or y > 150:
            if   x < 8   and y < 8:   x = 1;   y = 159
            elif x < 8   and y > 152: x = 239; y = 159
            elif x > 232 and y < 8:   x = 1;   y = 1
            elif x > 232 and y > 152: x = 239; y = 1
            elif x < 8:               x = 1;   y = 159
            elif x > 232:             x = 239; y = 1
            elif y < 8:               x = 1;   y = 1
            elif y > 152:             x = 239; y = 159
            else:logging.info('FLEE ERROR')
        else:pass
        pos = hlt.entity.Position(x,y)
        return pos
    
###############################################################################
    
def track_dock(shipid, planetid):
    committed_ships[shipid]=planetid
    docked_planets[planetid.id][1]+=1

def docking(shipid, planetid):
    try:del committed_ships[shipid];docked_planets[planetid.id][1]-=1;docked_planets[planetid.id][0]+=1
    except:pass
    
def track_defender(shipid, planet):
    docked_planets[planet.id][3]+=1
    committed_ships[shipid]=planet
    
###############################################################################
    
def nav_enemy(target_ship, minimum_distance=3,_ignore_ships = False):
    navigate_command = ship.navigate(ship.closest_point_to(target_ship,minimum_distance),
                game_map, speed=int(hlt.constants.MAX_SPEED),ignore_ships=_ignore_ships)
    if navigate_command:return navigate_command
    else:logging.info('Returning NONE Nav_Enemy'); return None
        
def nav_planet(target_planet):
    logging.info('nav planet {}'.format(target_planet))
    navigate_command = ship.navigate(ship.closest_point_to(target_planet),
                game_map,speed=int(hlt.constants.MAX_SPEED),ignore_ships=False)
    if navigate_command:return navigate_command
    else:logging.info('Returning NONE Nav_Planet');return None

###############################################################################

while True:

    round_counter += 1
    logging.info('Round number: {}'.format(round_counter))
    game_map = game.update_map()
    command_queue = []

    if init:
        _ship = game_map.get_me().all_ships()[0]
        entities_by_distance = game_map.nearby_entities_by_distance(_ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))        
        team_ships = game_map.get_me().all_ships()
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
        for ship in game_map.get_me().all_ships(): distance = hlt.entity.Entity.calculate_distance_between(ship,closest_enemy_ships[0])
        if len(closest_enemy_ships) > 3: logging.info('\n\n4 MAN')
        elif len(closest_enemy_ships) <= 3:
            if distance < 100: logging.info('\n\n2 MAN AGRESSIVE'); twos = 2
            else: logging.info('\n\n2 MAN PASSIVE'); twos = 1
        logging.info('Starting distance: {}'.format(distance))
        del _ship, distance
            
        #ESTABLISH INITAL SHIP IDS FOR MICROMANAGING START-PHASE
        for ship in game_map.get_me().all_ships():
            shipid = ship.id
            if len(starting_ship_ids) > 1: continue
            if shipid == 0: starting_ship_ids = [0,1,2]
            elif shipid == 3: starting_ship_ids = [3,4,5]
            elif shipid == 6: starting_ship_ids = [6,7,8]
            elif shipid == 9: starting_ship_ids = [9,10,11]
            else: logging.info('ERROR 0')
                
        #POPULATE DOCKING DICT
        planets = game_map.all_planets()
        #[Docked ships, Ships on the way, Total docking spots, Number of defenders we want, Number of defenders now]
        for planet in planets: docked_planets[planet.id] = [0,0,planet.num_docking_spots,2,0]

        #Micromanage starting orders by sending each ship to the optimal planet
        if twos != 2:
            twos_start = {}
            for ship in game_map.get_me().all_ships():
                entities_by_distance = game_map.nearby_entities_by_distance(ship)
                entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))  
                closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]    
                plan_dict = {}
                for planet in closest_empty_planets: plan_dict[planet.id]=hlt.entity.Entity.calculate_distance_between(ship,planet)
                twos_start[ship.id]=plan_dict
            #Create unique planet lists for each ship
            unique_planets = []
            for i in twos_start: unique_planets.append(set(twos_start[i]))
            possible_combinations = []
            corresponding_ids = []
            #Iterate through all possible combinations and store unique ones
#            logging.info('Unique planets: {}'.format(unique_planets[0]))
            for i in unique_planets[0]:
                for j in unique_planets[1]:
                    for h in unique_planets[2]:
                        try:
                            if len([i,j,h]) == len(set([i,j,h])):
                                possible_combinations.append([twos_start[starting_ship_ids[0]][i],
                                                              twos_start[starting_ship_ids[1]][j],
                                                              twos_start[starting_ship_ids[2]][h]])
                                corresponding_ids.append([i,j,h])
                            else: pass
                        except: pass
            #Find the minimum combination and it's index value to find planet id's
            summed_combinations = []
            for i in possible_combinations: summed_combinations.append(sum(i))
            corresponding_ids = corresponding_ids[list.index(summed_combinations, min(summed_combinations))]
            logging.info('Corresponding IDs: {}\nDistance: {}'.format(corresponding_ids,min(possible_combinations)))
            for planet in game_map.all_planets():
                if planet.id == corresponding_ids[0]: _plan_zero = planet
                if planet.id == corresponding_ids[1]: _plan_one = planet
                if planet.id == corresponding_ids[2]: _plan_two = planet
            committed_ships[starting_ship_ids[0]]=_plan_zero
            committed_ships[starting_ship_ids[1]]=_plan_one
            committed_ships[starting_ship_ids[2]]=_plan_two
            del twos_start, plan_dict, unique_planets, summed_combinations,_plan_one,_plan_two,_plan_zero,corresponding_ids
    
        #END OF INIT
        init = False
        
###############################################################################
################       STRATEGIES        ######################################
###############################################################################
    
    #PARAMS
    dominating       = False
    agressive_twos   = False
    losing           = False
    if len(game_map.get_me().all_ships()) > 55:                                         dominating     = True
    elif twos == 2:                                                                     agressive_twos = True
    elif len(game_map.get_me().all_ships()) < 10 and round_counter > 80 and twos == 0:  losing         = True

    #IF THERE ARE TOO MANY SHIPS WE SIMPLY ATTACK --> TO AVOID TIMING OUT
    if dominating == True:
        logging.info('Dominating')
        for ship in game_map.get_me().all_ships():
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                continue
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))                  
            team_ships = game_map.get_me().all_ships()
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
            if nav_enemy(closest_enemy_ships[0]):
                command_queue.append(nav_enemy(closest_enemy_ships[0],_ignore_ships = True))
        game.send_command_queue(command_queue)
        continue
   
    #AGRESSIVE TWOS
    elif agressive_twos:
        logging.info('Agressive Twos')
        for ship in game_map.get_me().all_ships():
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))                  
            team_ships = game_map.get_me().all_ships()
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
            if nav_enemy(closest_enemy_ships[0]):
                command_queue.append(nav_enemy(closest_enemy_ships[0],minimum_distance=4))
        game.send_command_queue(command_queue)
        continue  

    #FLEE
    elif losing:
        logging.info('Losing')
        for ship in game_map.get_me().all_ships():
            if ship.docking_status != ship.DockingStatus.UNDOCKED:command_queue.append(hlt.entity.Ship.undock(ship));continue
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))                  
            team_ships = game_map.get_me().all_ships()
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
            distance_to_nearest_enemy = hlt.entity.Entity.calculate_distance_between(ship, closest_enemy_ships[0])
            navigate_command = ship.navigate(escape(ship,closest_enemy_ships[0],distance_to_nearest_enemy),game_map, speed=int(hlt.constants.MAX_SPEED),ignore_ships=False)
            if navigate_command: command_queue.append(navigate_command)
        game.send_command_queue(command_queue)
        continue  
    
###############################################################################
################       MAIN STRATEGY        ######################################
###############################################################################
    else:
        for ship in game_map.get_me().all_ships():
            if ship.docking_status != ship.DockingStatus.UNDOCKED: 
                continue

            #MAIN-INIT-1
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
            team_ships = game_map.get_me().all_ships()
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
            distance_to_nearest_enemy = hlt.entity.Entity.calculate_distance_between(ship, closest_enemy_ships[0])
            
            #PARAMS
            dock_range = 19
            aggro_range = 16
            safe_dock                                                       = False
            immediate_orders                                                = False
            immediate_threat                                                = False
            if distance_to_nearest_enemy < aggro_range: immediate_threat    = True            
            elif ship.id in committed_ships: immediate_orders               = True
            if distance_to_nearest_enemy > dock_range: safe_dock            = True
            
            #IF CLOSE ENEMIES
            if immediate_threat:
                logging.info('Immediate Threat')
                if nav_enemy(closest_enemy_ships[0]):
                    command_queue.append(nav_enemy(closest_enemy_ships[0]))
                continue
            
            #OTHERWISE, IF CURRENT ORDERS EXIST
            elif immediate_orders:
                logging.info('Immediate Orders')
                if ship.can_dock(committed_ships[ship.id]):
                    if safe_dock:
                        command_queue.append(ship.dock(committed_ships[ship.id]))
                        docking(ship.id, committed_ships[ship.id])
                    else:
                        if nav_enemy(closest_enemy_ships[0]):
                            command_queue.append(nav_enemy(closest_enemy_ships[0]))
                else:
                    if nav_planet(committed_ships[ship.id]):
                        logging.info('Moving towards target')
                        command_queue.append(nav_planet(committed_ships[ship.id]))
                    else:
                        logging.info('ERROR 1')
                continue
            else:
                logging.info('NO ACTIVE COMMANDS')
            
            #MAIN-INIT-2
            closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]    
            closest_owned_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].is_owned()]
            if len(closest_owned_planets)>0: closest_owned_planet=closest_owned_planets[0]
            if len(closest_empty_planets)>1: distance_to_closest_empty_planet = hlt.entity.Entity.calculate_distance_between(ship, closest_empty_planets[0])

            #PARAMS
            percentage_to_leave = 0.10
            max_distance = 60
            close_empty_planets = False
            empty_docking_spots = False
            if ((len(closest_owned_planets) >= 2 and (docked_planets[closest_owned_planet.id][0]+(docked_planets[closest_owned_planet.id][1]) < docked_planets[closest_owned_planet.id][2]))): empty_docking_spots = True
            if ((len(closest_empty_planets) > int(len(game_map.all_planets())*percentage_to_leave) and (distance_to_closest_empty_planet < max_distance) and (docked_planets[closest_empty_planets[0].id][1]+docked_planets[closest_empty_planets[0].id][0] < docked_planets[closest_empty_planets[0].id][2]))): close_empty_planets = True            

            #IF THERE ARE UNDOCKED SPOTS
            if empty_docking_spots:
                logging.info('Empty Docking Spots')
                track_dock(ship.id,closest_owned_planet)
                if ship.can_dock(closest_owned_planet):
                    if safe_dock:
                        command_queue.append(ship.dock(closest_owned_planet))
                        docking(ship.id, closest_owned_planet)
                    else:
                        if nav_enemy(closest_enemy_ships[0]):
                            command_queue.append(nav_enemy(closest_enemy_ships[0]))
                else:
                    if nav_planet(closest_owned_planet):
                        command_queue.append(nav_planet(closest_owned_planet))
            
            #OTHERWISE, IF THERE ARE MANY EMPTY PLANETS, GO FOR THEM
            elif close_empty_planets:
                logging.info('Close Empty Planets')
                track_dock(ship.id, closest_empty_planets[0])
                if ship.can_dock(closest_empty_planets[0]):
                    if safe_dock:
                        command_queue.append(ship.dock(closest_empty_planets[0]))
                        docking(ship.id, closest_empty_planets[0])
                    else:
                        if nav_enemy(closest_enemy_ships[0]):
                            command_queue.append(nav_enemy(closest_enemy_ships[0]))
                else:
                    if nav_planet(closest_empty_planets[0]):
                        command_queue.append(nav_planet(closest_empty_planets[0]))
                    
            #OTHERWISE, FIND SHIPS TO ATTACK!
            else:
                logging.info('Nothing on - attacking')
                if nav_enemy(closest_enemy_ships[0]):
                    command_queue.append(nav_enemy(closest_enemy_ships[0]))

        #SEND COMMANDS
        logging.info('{}'.format(command_queue))
        game.send_command_queue(command_queue)
         
###############################################################################
    
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
                        
        