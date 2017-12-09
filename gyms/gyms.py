import discord
from discord.ext import commands
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, DocType, Text, Float, Keyword
from elasticsearch_dsl.connections import connections
from monacle_scraper import MonacleScraper, Team
from collections import defaultdict
from requests.exceptions import HTTPError
import humanize
import datetime
import re
import uuid
import trainerdex

RE_MENTION = re.compile('\<@\d+\>')

TEAM_COLORS = {
    0: 0xD3D3D3,
    1: 0x0000FF,
    2: 0xFF0000,
    3: 0xFFFF00
}

MOVES = defaultdict(lambda: '?', { #From https://github.com/Noctem/Monocle/blob/a2e3c61b2ddd7772ae3c62a6f252476cce0e804b/monocle/names.py#L261
    1: 'Thunder Shock',
    2: 'Quick Attack',
    3: 'Scratch',
    4: 'Ember',
    5: 'Vine Whip',
    6: 'Tackle',
    7: 'Razor Leaf',
    8: 'Take Down',
    9: 'Water Gun',
    10: 'Bite',
    11: 'Pound',
    12: 'Double Slap',
    13: 'Wrap',
    14: 'Hyper Beam',
    15: 'Lick',
    16: 'Dark Pulse',
    17: 'Smog',
    18: 'Sludge',
    19: 'Metal Claw',
    20: 'Vice Grip',
    21: 'Flame Wheel',
    22: 'Megahorn',
    23: 'Wing Attack',
    24: 'Flamethrower',
    25: 'Sucker Punch',
    26: 'Dig',
    27: 'Low Kick',
    28: 'Cross Chop',
    29: 'Psycho Cut',
    30: 'Psybeam',
    31: 'Earthquake',
    32: 'Stone Edge',
    33: 'Ice Punch',
    34: 'Heart Stamp',
    35: 'Discharge',
    36: 'Flash Cannon',
    37: 'Peck',
    38: 'Drill Peck',
    39: 'Ice Beam',
    40: 'Blizzard',
    41: 'Air Slash',
    42: 'Heat Wave',
    43: 'Twineedle',
    44: 'Poison Jab',
    45: 'Aerial Ace',
    46: 'Drill Run',
    47: 'Petal Blizzard',
    48: 'Mega Drain',
    49: 'Bug Buzz',
    50: 'Poison Fang',
    51: 'Night Slash',
    52: 'Slash',
    53: 'Bubble Beam',
    54: 'Submission',
    55: 'Karate Chop',
    56: 'Low Sweep',
    57: 'Aqua Jet',
    58: 'Aqua Tail',
    59: 'Seed Bomb',
    60: 'Psyshock',
    61: 'Rock Throw',
    62: 'Ancient Power',
    63: 'Rock Tomb',
    64: 'Rock Slide',
    65: 'Power Gem',
    66: 'Shadow Sneak',
    67: 'Shadow Punch',
    68: 'Shadow Claw',
    69: 'Ominous Wind',
    70: 'Shadow Ball',
    71: 'Bullet Punch',
    72: 'Magnet Bomb',
    73: 'Steel Wing',
    74: 'Iron Head',
    75: 'Parabolic Charge',
    76: 'Spark',
    77: 'Thunder Punch',
    78: 'Thunder',
    79: 'Thunderbolt',
    80: 'Twister',
    81: 'Dragon Breath',
    82: 'Dragon Pulse',
    83: 'Dragon Claw',
    84: 'Disarming Voice',
    85: 'Draining Kiss',
    86: 'Dazzling Gleam',
    87: 'Moonblast',
    88: 'Play Rough',
    89: 'Cross Poison',
    90: 'Sludge Bomb',
    91: 'Sludge Wave',
    92: 'Gunk Shot',
    93: 'Mud Shot',
    94: 'Bone Club',
    95: 'Bulldoze',
    96: 'Mud Bomb',
    97: 'Fury Cutter',
    98: 'Bug Bite',
    99: 'Signal Beam',
    100: 'X-Scissor',
    101: 'Flame Charge',
    102: 'Flame Burst',
    103: 'Fire Blast',
    104: 'Brine',
    105: 'Water Pulse',
    106: 'Scald',
    107: 'Hydro Pump',
    108: 'Psychic',
    109: 'Psystrike',
    110: 'Ice Shard',
    111: 'Icy Wind',
    112: 'Frost Breath',
    113: 'Absorb',
    114: 'Giga Drain',
    115: 'Fire Punch',
    116: 'Solar Beam',
    117: 'Leaf Blade',
    118: 'Power Whip',
    119: 'Splash',
    120: 'Acid',
    121: 'Air Cutter',
    122: 'Hurricane',
    123: 'Brick Break',
    124: 'Cut',
    125: 'Swift',
    126: 'Horn Attack',
    127: 'Stomp',
    128: 'Headbutt',
    129: 'Hyper Fang',
    130: 'Slam',
    131: 'Body Slam',
    132: 'Rest',
    133: 'Struggle',
    134: 'Scald',
    135: 'Hydro Pump',
    136: 'Wrap',
    137: 'Wrap',
    200: 'Fury Cutter',
    201: 'Bug Bite',
    202: 'Bite',
    203: 'Sucker Punch',
    204: 'Dragon Breath',
    205: 'Thunder Shock',
    206: 'Spark',
    207: 'Low Kick',
    208: 'Karate Chop',
    209: 'Ember',
    210: 'Wing Attack',
    211: 'Peck',
    212: 'Lick',
    213: 'Shadow Claw',
    214: 'Vine Whip',
    215: 'Razor Leaf',
    216: 'Mud Shot',
    217: 'Ice Shard',
    218: 'Frost Breath',
    219: 'Quick Attack',
    220: 'Scratch',
    221: 'Tackle',
    222: 'Pound',
    223: 'Cut',
    224: 'Poison Jab',
    225: 'Acid',
    226: 'Psycho Cut',
    227: 'Rock Throw',
    228: 'Metal Claw',
    229: 'Bullet Punch',
    230: 'Water Gun',
    231: 'Splash',
    232: 'Water Gun',
    233: 'Mud Slap',
    234: 'Zen Headbutt',
    235: 'Confusion',
    236: 'Poison Sting',
    237: 'Bubble',
    238: 'Feint Attack',
    239: 'Steel Wing',
    240: 'Fire Fang',
    241: 'Rock Smash',
    242: 'Transform',
    243: 'Counter',
    244: 'Powder Snow',
    245: 'Close Combat',
    246: 'Dynamic Punch',
    247: 'Focus Blast',
    248: 'Aurora Beam',
    249: 'Charge Beam',
    250: 'Volt Switch',
    251: 'Wild Charge',
    252: 'Zap Cannon',
    253: 'Dragon Tail',
    254: 'Avalanche',
    255: 'Air Slash',
    256: 'Brave Bird',
    257: 'Sky Attack',
    258: 'Sand Tomb',
    259: 'Rock Blast',
    260: 'Infestation',
    261: 'Struggle Bug',
    262: 'Silver Wind',
    263: 'Astonish',
    264: 'Hex',
    265: 'Night Shade',
    266: 'Iron Tail',
    267: 'Gyro Ball',
    268: 'Heavy Slam',
    269: 'Fire Spin',
    270: 'Overheat',
    271: 'Bullet Seed',
    272: 'Grass Knot',
    273: 'Energy Ball',
    274: 'Extrasensory',
    275: 'Future Sight',
    276: 'Mirror Coat',
    277: 'Outrage',
    278: 'Snarl',
    279: 'Crunch',
    280: 'Foul Play',
    281: 'Hidden Power'
})


class Gym(DocType):
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    description = Text(analyzer='snowball')
    latitude = Float()
    longitude = Float()
    url = Text()
    image = Text()
    monacle_id = Text()

    class Meta:
        index = 'marker'

                
def format_list(items):
    if len(items) > 1:
        message = ", ".join([item for item in items[:-1]])+" and {0}".format(items[-1])
    else:
        message = "{0}".format(items[0])
    return message

def get_display_name(member):
    try:
        return trainerdex.Client().get_discord_user(member.id).owner().trainer(all_=False).username
    except:
        return member.display_name

connections.create_connection(hosts=['localhost'])

class Gyms:
    """Pokemon Go Gyms!"""

    def __init__(self, bot):
        self.bot = bot
        self.client = Elasticsearch()
        self.monacle = MonacleScraper('https://kentpogomap.uk/raw_data', 'BIDoJSaHxR0Cz3mqJvI5kShtUc0CW/HPwK/CrRtEZhU=')
        self.going_users = defaultdict(set) # gym.id: list of users
        self.arrived_users = defaultdict(set) # gym.id: list of users
        self.users_going = {} # user_id: gym.id
        self.users_arrived = {} # user_id: gym.id
        self.user_groups = defaultdict(set) # user_id: list of users
		
    async def find_gym(self, gym):
        s = Search(using=self.client, index="marker").query("match", title={'query': gym, 'fuzziness': 2, 'slop': 1})
        response = s.execute()
        if response.hits.total == 0:
            await self.bot.say("I couldn't find that gym")
            return None, None
        hit = response[0]
        monacle_gym = await self.get_monacle_gym(hit)
        return hit, monacle_gym

    async def get_monacle_gym(self, hit):
        return None

    @commands.command(pass_context=True)
    async def gym(self, ctx, *, gym: str):
        """
        Lookup a gym, responds with an image, title, description and a google maps link.
        Gyms that have active raids are prioritized over gyms that do not.
        """
        hit, monacle_gym = await self.find_gym(gym)
        if not hit:
            return
        description = "{}\n[Get Directions](https://www.google.com/maps/?daddr={},{})".format(hit.description, hit.latitude, hit.longitude)
        embed=discord.Embed(title=hit.title, url='https://www.pokemongomap.info'+hit.url, description=description)
        embed.set_thumbnail(url=hit.image)
        if monacle_gym:
            embed.set_image(url='https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&zoom=15&size=250x125&maptype=roadmap&markers=color:{3}%7C{0},{1}&key={2}'.format(hit.latitude, hit.longitude, 'AIzaSyCEadifeA8X02v2OKv-orZWm8nQf1Q2EZ4', "0x{:02X}".format(TEAM_COLORS[monacle_gym.team])))
            embed.color = TEAM_COLORS[monacle_gym.team]
            if monacle_gym.slots_available > 0:
                embed.add_field(name='Slots available', value=monacle_gym.slots_available)
            embed.add_field(name='Owned by', value=monacle_gym.team_name)
            if monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
                embed.add_field(name='Raid level', value=monacle_gym.raid_level)
                embed.add_field(name='Raid Pokemon', value=monacle_gym.raid_pokemon.name)
                embed.add_field(name='CP', value=monacle_gym.raid_pokemon.cp)
                embed.add_field(name='Moveset', value=MOVES[monacle_gym.raid_pokemon.move_1]+' / '+MOVES[monacle_gym.raid_pokemon.move_2])
                embed.add_field(name='Started at', value=monacle_gym.raid_start.strftime("%H:%M:%S"))
                embed.add_field(name='Ends at', value="{} ({})".format(monacle_gym.raid_end.strftime("%H:%M:%S"), humanize.naturaltime(datetime.datetime.now()-monacle_gym.raid_end)))
        else:
            embed.set_image(url='https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&zoom=15&size=250x125&maptype=roadmap&markers=color:{3}%7C{0},{1}&key={2}'.format(hit.latitude, hit.longitude, 'AIzaSyCEadifeA8X02v2OKv-orZWm8nQf1Q2EZ4', 'white'))

        await self.bot.say(embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    async def interested(self, ctx, *, gym: str):
        """State you're interested in going to a raid"""
        gym = re.sub(RE_MENTION, '', gym).strip()
        hit, monacle_gym = await self.find_gym(gym)
        if not hit:
            return
        message = get_display_name(ctx.message.author)
        if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
            message += " is interested in the {0} raid".format(monacle_gym.raid_pokemon.name)
        else:
            await self.bot.say("I can't see a raid at {}, sorry.".format(hit.title))
            return self.bot.delete_message(ctx.message)
        message += ' at {}'.format(hit.title)
        message += "."
        await self.bot.say(message)
        if discord.utils.get(ctx.message.server.channels, name='ticker'):
            ticker = discord.utils.get(ctx.message.server.channels, name='ticker')
            await self.bot.send_message(ticker, message)
        await self.bot.delete_message(ctx.message)
        
    @commands.command(pass_context=True, no_pm=True)
    async def addgoing(self, ctx, *, gym: str):
        """Used to set other trainers as going to a raid"""
        return await self._going(ctx, gym, False)

    @commands.command(pass_context=True, no_pm=True)
    async def going(self, ctx, *, gym: str):
        """Used to set yourself and possibly other trainers as going to a raid"""
        return await self._going(ctx, gym, True)

    async def _going(self, ctx, gym, add_author_to_group):
        gym = re.sub(RE_MENTION, '', gym).strip()
        hit, monacle_gym = await self.find_gym(gym)
        if ctx.message.author in dict(list(self.users_going.items()) + list(self.users_arrived.items())) and add_author_to_group:
            await self._notgoing(ctx)
            temp1 = await self.bot.say('You forgot to do `.done` at your last raid but I sorted that.')
        extra_users = re.search(r'\+(\d+)', gym)
        if not hit:
            return
        message = get_display_name(ctx.message.author)
        if extra_users:
            extra_users = int(extra_users.group(0))
            message += " +{}".format(extra_users)
        else:
            extra_users = 0
            
        if add_author_to_group:
            self.going_users[hit.meta.id].add(ctx.message.author)
        group = set()
        users = []
        if add_author_to_group:
            group.add(ctx.message.author)
            users.append(ctx.message.author)
        if ctx.message.mentions:
            group.update(ctx.message.mentions)
            users = list(group) # remove duplicates
            if ctx.message.author in ctx.message.mentions:
                users.remove(ctx.message.author) # can't raid with yourself
            for user in users:
                self.going_users[hit.meta.id].add(user)
            message = format_list(["{0}".format(get_display_name(user)) for user in users])

        if len(users) == 1:
            message += ' is'
        else:
            message += ' are'
        
        message += ' going to {}'.format(hit.title)
        if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
            message += " for a raid on {0}".format(monacle_gym.raid_pokemon.name)
        message += "."

        for user in users:
            self.users_going[user] = hit.meta.id
            self.user_groups[user].update(group)
        await self.bot.say(message)
        if discord.utils.get(ctx.message.server.channels, name='ticker'):
            ticker = discord.utils.get(ctx.message.server.channels, name='ticker')
            await self.bot.send_message(ticker, message)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True, no_pm=True)
    async def notgoing(self, ctx):
        """No, not going anymore m8"""
        message = await self._notgoing(ctx)
        await self.bot.say(message)
        if discord.utils.get(ctx.message.server.channels, name='ticker'):
            ticker = discord.utils.get(ctx.message.server.channels, name='ticker')
            await self.bot.send_message(ticker, message)
        return await self.bot.delete_message(ctx.message)

    async def _notgoing(self, ctx):
        gym_id = self.users_arrived.get(ctx.message.author, None)
        if not gym_id:
            gym_id = self.users_going.get(ctx.message.author, None)
        if not gym_id:
            await self.bot.say('You are not marked as going to any raids')
            return
        gym = Gym.get(id=gym_id)
        monacle_gym = await self.get_monacle_gym(gym)
        if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
            message = "{} is not going to the {} raid at {}".format(get_display_name(ctx.message.author), monacle_gym.raid_pokemon.name, gym.title)
        else:
            message = "{} is not going to {}".format(get_display_name(ctx.message.author), gym.title)
        self.arrived_users[gym_id].discard(ctx.message.author)
        self.going_users[gym_id].discard(ctx.message.author)
        if ctx.message.author in self.users_arrived:
            del self.users_arrived[ctx.message.author]
        if ctx.message.author in self.users_going:
            del self.users_going[ctx.message.author]
        for user in self.user_groups[ctx.message.author]:
            if user != ctx.message.author:
                self.user_groups[user].discard(ctx.message.author)
        del self.user_groups[ctx.message.author]
        return message

    @commands.command(pass_context=True)
    async def who(self, ctx, *, gym: str):
        """
        People try to put us down
        Just because we get around
        Things they do look awful cold
        I hope I die before I get old
        """
        hit, monacle_gym = await self.find_gym(gym)
        if not hit:
            return
        message = ""
        if len(self.going_users[hit.meta.id]) == 0 and len(self.arrived_users[hit.meta.id]) == 0:
            message = "Nobody is going"
        if len(self.going_users[hit.meta.id]) > 0:
            message += format_list([get_display_name(user) for user in self.going_users[hit.meta.id]])
            message += " are" if len(self.going_users[hit.meta.id]) > 1 else " is"
            message += " on the way"
        if len(self.arrived_users[hit.meta.id]) > 0 and len(self.going_users[hit.meta.id]) > 0:
            message += " and "
        if len(self.arrived_users[hit.meta.id]) > 0:
            message += format_list([get_display_name(user) for user in self.arrived_users[hit.meta.id]])
            message += " have arrived at"
        else: 
            message += " to"
        if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
            message += " the {} raid at {}.\n".format(monacle_gym.raid_pokemon.name, hit.title)
        else:
            message += " "+hit.title
        await self.bot.say(message)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def arrived(self, ctx, *members: discord.Member):
        """You know when you were at school and they would do the register and you'd get really paranoid about how you said 'here'. No worries here, only one way to say it- [p]arrived!"""
        gym_id = self.users_arrived.get(ctx.message.author, None)
        if not gym_id:
            gym_id = self.users_going.get(ctx.message.author, None)
        if not gym_id:
            await self.bot.say('You are not marked as going to any raids')
            return
        gym = Gym.get(id=gym_id)
        monacle_gym = await self.get_monacle_gym(gym)
        arrived = set(self.user_groups[ctx.message.author])
        for member in members:
            arrived.update(self.user_groups[member])
        message = format_list([get_display_name(user) for user in arrived])
        if len(arrived) == 1:
            message += ' has'
        else:
            message += ' have'
        message += ' arrived at {}'.format(gym.title)
        if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
            message += " for the raid on {0}".format(monacle_gym.raid_pokemon.name)
        message += "."
        self.users_arrived[ctx.message.author] = gym_id
        for user in arrived:
            if user in self.user_groups:
                del self.user_groups[user]
            if user in self.users_going:
                del self.users_going[user]
            self.arrived_users[gym_id].add(user)
            self.going_users[gym_id].remove(user)
        await self.bot.say(message)
        if discord.utils.get(ctx.message.server.channels, name='ticker'):
            ticker = discord.utils.get(ctx.message.server.channels, name='ticker')
            await self.bot.send_message(ticker, message)
        await self.bot.delete_message(ctx.message)
		
    @commands.command(pass_context=True)
    async def done(self, ctx):
        """Finished already? That was quick!"""
        gym_id = self.users_arrived.get(ctx.message.author, None)
        if not gym_id:
            gym_id = self.users_going.get(ctx.message.author, None)
        if not gym_id:
            await self.bot.say('You are not marked as going to any raids')
            return
        gym = Gym.get(id=gym_id)
        monacle_gym = await self.get_monacle_gym(gym)
        if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
            message = "{} has finished the {} raid at {}".format(get_display_name(ctx.message.author), monacle_gym.raid_pokemon.name, gym.title)
        else:
            message = "{} is finished at {}".format(get_display_name(ctx.message.author), gym.title)
        self.arrived_users[gym_id].discard(ctx.message.author)
        self.going_users[gym_id].discard(ctx.message.author)
        if ctx.message.author in self.users_arrived:
            del self.users_arrived[ctx.message.author]
        if ctx.message.author in self.users_going:
            del self.users_going[ctx.message.author]
        for user in self.user_groups[ctx.message.author]:
            if user != ctx.message.author:
                self.user_groups[user].discard(ctx.message.author)
        del self.user_groups[ctx.message.author]
        await self.bot.say(message)
        if discord.utils.get(ctx.message.server.channels, name='ticker'):
            ticker = discord.utils.get(ctx.message.server.channels, name='ticker')
            await self.bot.send_message(ticker, message)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def raids(self, ctx):
        """Not a list of active raids"""
        message = ''
        gyms = set(list(self.going_users.keys())+list(self.arrived_users.keys()))
        if not gyms:
            message = 'There are no raids on at the moment'
        for gym_id in gyms:
            gym = Gym.get(id=gym_id)
            monacle_gym = await self.get_monacle_gym(gym)
            if monacle_gym and monacle_gym.raid_start and monacle_gym.raid_start <= datetime.datetime.now() and monacle_gym.raid_end >= datetime.datetime.now():
                num_users = len(self.going_users[gym_id]) + len(self.arrived_users[gym_id])
                message += str(num_users)
                if num_users == 1:
                    message += ' user is'
                else:
                    message += ' users are'
                message += ' on the way to the {} raid at {} - ends at {} ({}).\n'.format(monacle_gym.raid_pokemon.name, gym.title, monacle_gym.raid_end.strftime("%H:%M:%S"), humanize.naturaltime(datetime.datetime.now()-monacle_gym.raid_end))
        await self.bot.say(message)
        await self.bot.delete_message(ctx.message)
            
        
def setup(bot):
    bot.add_cog(Gyms(bot))
