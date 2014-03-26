## Warlight AI Challenge Python Protocol

Warlight python protocol is design to help implement AI bots a lot easier without
having to worry about the nitty gritty of the protocol behind the scenes.  Handler provides a clean interface for you to perform your bots function and logic a number of events throughout the match.

### What is Warlight AI Challenge?

Warlight AI Challenge is a turn based game which is similiar to the board game 
"Risk" where the opponents need to create their own AI bot to play defeat each other
within the least amount of rounds possible. More information can be found at: <http://theaigames.com/competitions/warlight-ai-challenge/>

### Usage

Just extend the warlight handler and add your own AI logic. After that define an
Engine with your handler as a parameter and tell the engine to run.

```python
from warlight import Engine, Handler


class MyBot(Handler):

    def on_pick_starting_regions(self, engine, time, regions):
        engine.do_no_moves()

    def on_me_place_armies(self, engine, time):
        engine.do_no_moves()

    def on_me_attack_or_transfer(self, engine, time):
        engine.do_no_moves()


if __name__ == "__main__":
    engine = Engine(MyBot())
    engine.run()
```

You can easily check if you are the owner of a region:

```python

if region.owner == engine.me
```

You can also check if you are not the owner:

```python
if region.owner in [engine.opponent, 'neutral']
```

Using the engine easily place your units:

```python
engine.do_placements(region, units)
```

It's also easy to attack or transfer units from a region to a neighbour:

```python
engine.do_attack_or_transfer(region, neighbour, region.armies - 1)
```
    

Logging can be done like this (it will appear as an error at the top of the match dump):

```python
engine.log("this won't crash the bot")
```

### TODO:
Provide some unit tests of some kind.
        
### Credits
Written by Kevin Woodland while working at Byte Orbit <http://www.byteorbit.com/>

### Contact
Twitter: @kevelbreh
