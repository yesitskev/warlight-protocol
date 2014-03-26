"""
Copyright (c) 2014, Kevin Woodland

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
import re


def event(regex):
    """
    Add an event regex to be matched against the protocol event message
    """
    def wrap(function):
        function.pattern = re.compile(regex, re.IGNORECASE)
        return function
    return wrap


def event_item(regex):
    """
    Add inner regex grouping for repeating expressions within the event expression result.
    """
    def wrap(function):
        function.sub_pattern = re.compile(regex, re.IGNORECASE)
        return function
    return wrap


class Region(object):
    """
    An object representing a region. Contains a list of neighbors linking
    to other regions which this region borders as well as the super region
    this region belongs to.  Current owner and army count is also stored.
    """

    def __init__(self, region_id, super_region):
        self.region_id = region_id
        self.super_region = super_region
        self.armies = 0
        self.owner = 'neutral'
        self.neighbours = []
        self.extras = {}


class SuperRegion(object):
    """
    A super region containing a list of regions which create up the entirety
    of the super region. Also contains information about the army reward bonus.
    """

    def __init__(self, super_region_id, reward):
        self.super_region_id = super_region_id
        self.reward = reward
        self.regions = []
        self.extras = {}


class Handler(object):

    def per_setup_super_region(self, engine, super_region, reward):
        """
        Called after a new super region has been added.
        """
        pass

    def on_setup_super_region(self, engine):
        """
        Called after all super regions have been added.
        """
        pass

    def per_setup_region(self, engine, super_region, region):
        """
        Region has been added to a super region.
        """
        pass

    def on_setup_region(self, engine):
        """
        Regions have finished being added.
        """
        pass

    def per_setup_neighbor(self, engine, region, neighbor):
        """
        Neighbour has been added to a region.
        """
        pass

    def on_setup_neighbor(self, engine):
        """
        Neighbours have finished being added.
        """
        pass

    def on_setting_me(self, engine, name):
        """
        This bots name has been given.
        """
        pass

    def on_setting_opponent(self, engine, name):
        """
        Opponent bot name is given.
        """
        pass

    def on_setting_starting_armies(self, engine, armies):
        """
        Starting army count for the round has been set.
        """
        pass

    def on_pick_starting_regions(self, engine, time, regions):
        """
        Bot given a choice of regions to choose from.
        """
        pass

    def per_update_map(self, engine, region, player, armies):
        """
        Region has been updated with owner and army count.
        """
        pass

    def on_update_map(self, engine):
        """
        Map has been updated.
        """
        pass

    def per_opponent_place_armies(self, engine, region, armies):
        """
        Opponent placed armies in a region
        """
        pass

    def on_opponent_place_armies(self, engine):
        """
        Opponent has finished placing armies.
        """
        pass

    def per_opponent_attack_or_move(self, engine, region, armies):
        """
        Opponent attack or moved armies to a region.
        """
        pass

    def on_opponent_attack_or_move(self, engine):
        """
        Opponent has finished attacking or moving.
        """
        pass

    def on_go_place_armies(self, engine, time):
        """
        Bots turn to place armies.
        """
        raise NotImplementedError

    def on_go_attack_or_transfer(self, engine, time):
        """
        Bots turn to attack or transfer
        """
        raise NotImplementedError


class Engine(object):

    def __init__(self, handler):
        self.handler = handler
        self.handler_methods = []
        self.responses = []
        self.super_regions = {}
        self.regions = {}
        self.me = None
        self.opponent = None
        self.starting_armies = 0
        self.handler_methods = [method for method in dir(self)
                                if callable(getattr(self, method)) and re.search('^(on_*.)', method, re.IGNORECASE)]

    def run(self):
        while not sys.stdin.closed:
            try:
                message = sys.stdin.readline()

                # Ignore message of no length
                if len(message) == 0:
                    continue

                # Parse the message.
                self._parse(message)

            except KeyboardInterrupt:
                return
            except EOFError:
                return

    def _parse(self, message):
        """
        Find all message handlers defined in the Engine that are able of handling the message. If a sub pattern is
        found then find all occurrences and pass into the message handler as a parameter.

        """
        for method in self.handler_methods:
            temp = getattr(self, method)
            pattern = getattr(temp, 'pattern', False)
            match = pattern.search(message)

            # Make sure that there is a match for this method.
            if match is not None:
                group = match.group(1)
                sub_pattern = getattr(temp, 'sub_pattern', False)

                # If sub pattern matches are found then add list argument, else just
                # pass the original matching group.
                if sub_pattern:
                    groups = re.findall(sub_pattern, group)
                    temp(groups)
                else:
                    temp(group)

    def log(self, message):
        """
        Log an error through the standard error stream.
        """
        sys.stderr.write(message + '\n')
        sys.stderr.flush()

    def respond(self):
        """
        Join the responses by spaces and write the result to the standard output.
        """
        if len(self.responses) == 0:
            self.do_no_moves()

        sys.stdout.write(",".join(self.responses) + '\n')
        sys.stdout.flush()
        self.responses = []

    def add_response(self, message):
        """
        Add a response message to the response list.
        """
        self.responses.append(message)

    def do_no_moves(self):
        """
        Respond with 'No moves' to signify that no moves will be made.
        """
        self.responses = ["No moves"]

    def do_starting_regions(self, regions):
        """
        Respond with a list of regions.
        """
        self.responses = [" ".join(str(n) for n in regions)]

    def do_placements(self, region, troop_count):
        """
        Add a response for placing troops on a defined region.
        """
        self.add_response("%s place_armies %s %s" % (self.me, region.region_id, troop_count))

    def do_attack_or_transfer(self, source, target, troop_count):
        """
        Add a response for attacking or transferring troops from source region to target region.
        """
        self.add_response("%s attack/transfer %s %s %s" % (self.me, source.region_id, target.region_id, troop_count))

    @event("^setup_map\\s+super_regions\\s+(.*)")
    @event_item("(\\d+\\s+\\d)")
    def on_setup_map_super_regions(self, super_regions):
        """
        Engine returns super regions and their rewards.
        """
        for super_region in super_regions:
            split = super_region.split(" ")
            new_super_region = SuperRegion(split[0], split[1])
            self.super_regions[split[0]] = new_super_region
            self.handler.per_setup_super_region(self, new_super_region, split[1])
        self.handler.on_setup_super_region(self)

    @event("^setup_map\\s+regions\\s+(.*)")
    @event_item("(\\d+\\s+\\d)")
    def on_setup_map_regions(self, regions):
        """
        Engine returns regions for the map.
        """
        for region in regions:
            split = region.split(" ")
            super_region = self.super_regions[split[1]]
            new_region = Region(split[0], super_region)
            self.regions[split[0]] = new_region
            self.handler.per_setup_region(self, super_region, new_region)
        self.handler.on_setup_region(self)

    @event("^setup_map\\s+neighbors\\s+(.*)")
    @event_item("(\\d+\\s+(?:[0-9,]*))")
    def on_setup_map_neighbors(self, neighbors):
        """
        Engine returns a list of region ids with its neighbours. Update our regions to link together if they are
        neighbours.
        """
        for block in neighbors:
            split = block.split(" ")
            region = self.regions[split[0]]
            region_neighbors = split[1].split(",")

            for neighbor in region_neighbors:
                new_neighbor = self.regions[neighbor]
                region.neighbours.append(new_neighbor)
                new_neighbor.neighbours.append(region)
                self.handler.per_setup_neighbor(self, region, new_neighbor)

        self.handler.on_setup_neighbor(self)

    @event("^settings\\s+your_bot\\s+((?:[a-z][a-z0-9_]*))")
    def on_settings_your_bot(self, name):
        """
        Engine returns the this bots name.
        """
        self.me = name
        self.handler.on_setting_me(self, name)

    @event("^settings\\s+opponent_bot\\s+((?:[a-z][a-z0-9_]*))")
    def on_settings_opponent_bot(self, name):
        """
        Engine returns the opponent bots name.
        """
        self.opponent = name
        self.handler.on_setting_opponent(self, name)

    @event("^settings\\s+starting_armies\\s+(\\d+)")
    def on_settings_starting_armies(self, armies):
        """
        Engine returns the amount of armies that the bot can place in this round.
        """
        self.starting_armies = int(armies)
        self.handler.on_setting_starting_armies(self, int(armies))

    @event("^update_map\\s+(.*)")
    @event_item("(\\d+\\s+(?:[a-z][a-z0-9_]*)\\s+\\d+)")
    def on_update_map(self, updates):
        """
        Engine returns a bunch of updates.  Update each regions owner and army count.
        """
        for update in updates:
            split = update.split(" ")
            region = self.regions[split[0]]
            region.owner = split[1]
            region.armies = int(split[2])
            self.handler.per_update_map(self, region, region.owner, region.armies)
        self.handler.on_update_map(self)

    @event("^opponent_moves\\s+(.*)")
    @event_item("((?:[a-z][a-z0-9_]*)\\s+(?:place_armies|attack\\/transfer)\\s+\\d+\\s+\\d+)")
    def on_opponent_moves(self, args):
        """
        Engine returns all the opponent moves whether it is an army placement or a move/transfer.
        """
        placements = []
        attacks_or_transfers = []

        # Filter placements and attack/transfers into their own lists.
        for block in args:
            temp = block.split(' ')
            if temp[1] is 'place_armies':
                placements.append(block)
            elif temp[1] is 'attack/transfer':
                attacks_or_transfers.append(block)

        # Update regions with additional armies.
        for block in placements:
            temp = block.split(' ')
            region = self.regions[temp[2]]
            armies = int(temp[3])
            #region.armies += armies
            self.handler.per_opponent_place_armies(self, region, armies)
        self.handler.on_opponent_place_armies(self)

        # Call handler method for attack or transfers.
        for block in attacks_or_transfers:
            temp = block.split(' ')
            region = self.regions[temp[2]]
            armies = int(temp[3])
            self.handler.per_opponent_attack_or_move(self, region, armies)
        self.handler.on_opponent_attack_or_move(self)

    @event("^pick_starting_regions\\s+(.*)")
    @event_item("(\\d+)")
    def on_pick_starting_regions(self, regions):
        """
        Engine giving us a list of regions to pick from.
        """
        time = regions[0]

        # Construct a list of proper region objects. Index 0 is excluded because
        # that is the the the time we have to pick our regions.
        temp_regions = []
        for x in range(1, len(regions)):
            temp_regions.append(self.regions[regions[x]])
        self.handler.on_pick_starting_regions(self, time, temp_regions)
        self.respond()

    @event("^go\\s+place_armies\\s+(\\d+)")
    def on_go_place_armies(self, time=0):
        """
        Engine notifying us that it is our turn to place armies.
        """
        self.handler.on_go_place_armies(self, time)
        self.respond()

    @event("^go\\s+attack\\/transfer\\s+(\\d+)")
    def on_go_attack_or_transfer(self, time=0):
        """
        Engine notifying us that it is our turn to attack or transfer.
        """
        self.handler.on_go_attack_or_transfer(self, time)
        self.respond()
