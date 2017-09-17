import os
import asyncio
import time
import datetime
import discord
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
from TrainerDex import Requests

settings_file = 'data/trainerdex/settings.json'
json_data = dataIO.load_json(settings_file)
token = json_data['token']
r = Requests(token)

class Calls:
	"""Useful tools"""
	
	def getName(discord):
		return TrainerDex.getTrainerID(discord=discord.id).username if TrainerDex.getTrainerID(discord=discord.id).username else discord.display_name
	
	def getMember(ussername):
		return TrainerDex.getTrainerID(username=username).discord_ID

class TrainerDex:
	
	def __init__(self, bot):
		self.bot = bot
		self.teams = r.getTeams()
		
	async def getTrainerID(self, username=None, discord=None, account=None, prefered=True):
		listTrainers = r.listTrainers()
		for trainer in listTrainers:
			if username:
				if trainer.username==username:
					return trainer
			elif discord:
				if trainer.discord==discord and trainer.prefered is True:
					return trainer
			elif account:
				if trainer.account==account and trainer.prefered is True:
					return trainer
			else:
				return None
		
	async def getTeamByName(self, team):
		for item in self.teams:
			if item.name.title()==team.title():
				return item
		
	async def profileCard(self, name, force=False):
		trainer = await self.getTrainerID(username=name)
		if trainer.account is not None:
			account = r.getUser(trainer.account)
		else:
			account = None
		discordUser = trainer.discord
		trainer = r.getTrainer(trainer.id)
		team = self.teams[int(trainer.team)]
		level=r.trainerLevels(xp=trainer.xp)
		if trainer.statistics is False and force is False:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			embed=discord.Embed(description="**"+trainer.username+"**", timestamp=trainer.xp_time, colour=int(team.colour.replace("#", ""), 16))
			if account and (account.first_name or account.last_name):
				embed.add_field(name='Name', value=account.first_name+' '+account.last_name)
			embed.add_field(name='Team', value=team.name)
			embed.add_field(name='Level', value=level)
			embed.add_field(name='XP', value=int(trainer.xp) - int(r.trainerLevels(level=level)))
			embed.set_thumbnail(url=team.image)
			if trainer.cheater is True:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(trainer.username))
			embed.set_footer(text="Total XP: "+str(trainer.xp))
			await self.bot.say(embed=embed)
	
	async def _addProfile(self, mention, username, xp, team, start_date=None, has_cheated=False, currently_cheats=False, name=None, prefered=True):
		#Check existance
		listTrainers = r.listTrainers()
		for trainer in listTrainers:
			if trainer.username==username:
				await self.bot.say("A record already exists in the database for this trainer")
				await self.profileCard(name=trainer.username, force=True)
				return
		#Create or get auth.User
		#Create or update discord user
		listDiscordUsers = r.listDiscordUsers()
		discordUser=None
		if mention.avatar_url=='' or mention.avatar_url is None:
			avatarUrl = mention.default_avatar_url
		else:
			avatarUrl = mention.avatar_url
		for item in listDiscordUsers:
			if item.discord_id==mention.id:
				discordUser=item
		if discordUser is None:
			user = r.addUserAccount(username='_'+username, first_name=name)
			discordUser = r.addDiscordUser(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=avatarUrl, creation=mention.created_at, user=user)
		elif discordUser.discord_id==mention.id:
			user = discordUser.account_id
			discordUser = r.patchDiscordUser(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=avatarUrl, creation=mention.created_at)
		#create or update trainer
		trainer = r.addTrainer(username=username, team=team, start_date=start_date, has_cheated=has_cheated, currently_cheats=currently_cheats, prefered=prefered, account=user)
		#create update object
		update = r.addUpdate(trainer, xp)
		return user, discordUser, trainer, update


#Public Commands
	
	@commands.command(pass_context=True, name="trainer")
	async def trainer(self, ctx, trainer): 
		"""Trainer lookup"""
		await self.bot.send_typing(ctx.message.channel)
		await self.profileCard(trainer)

	@commands.group(pass_context=True)
	async def update(self, ctx):
		"""Update information about your TrainerDex profile"""
			
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
		
	@update.command(name="xp", pass_context=True)
	async def xp(self, ctx, xp: int, profile=None): 
		"""XP"""
		await self.bot.send_typing(ctx.message.channel)
		if profile==None:
			trainer = await self.getTrainerID(discord=ctx.message.author.id)
		else:
			trainer = await self.getTrainerID(username=profile)
			if trainer.discord_ID!=ctx.message.author.id:
				trainer = None
				return await self.bot.say("Cannot find an account called {} belonging to <@{}>.".format(profile,ctx.message.author.id))
		if trainer is not None:
			trainer = r.getTrainer(trainer.id)
			if int(trainer.xp) >= int(xp):
				await self.bot.say("Error: You last set your XP to {xp}, please try a higher number. `ValidationError: {usr}, {xp}`".format(usr= trainer.username, xp=trainer.xp))
				return
		print(trainer)
		update = r.addUpdate(trainer.id, xp)
		await self.profileCard(trainer.username)
		
	@update.command(name="name", pass_context=True)
	async def name(self, ctx, first_name, last_name=None): 
		"""
		Set your name in form of <first_name> <last_name>
		If you want to blank your last name set it to two dots '..'
		"""
		await self.bot.send_typing(ctx.message.channel)
		account = await self.getTrainerID(discord=ctx.message.author.id)
		if last_name=='..':
			last_name=' '
		if account:
			r.patchUserAccount(account.account, first_name=first_name, last_name=last_name)
			await self.profileCard(account.username)
		else:
			await self.bot.say("Not found!")
			return

	@update.group(name="goal", pass_context=True)
	async def goal(self, ctx):
		"""Update your goals"""
			
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
		
	@goal.command(name="daily", pass_context=True)
	async def daily(self, ctx, goal: int): 
		"""Daily Goal - Disabled"""
		await self.bot.say("Goals are currently disabled. Sorry.")
	
	@goal.command(name="total", pass_context=True)
	async def total(self, ctx, goal: int): 
		"""Total Goal - Disabled"""
		await self.bot.say("Goals are currently disabled. Sorry.")

#Mod-commands

#	@commands.command(pass_context=True)
#	@checks.mod_or_permissions(assign_roles=True)
#	async def spoofer(self, ctx, mention):
#		"""oh look, a cheater"""
#		await self.bot.send_typing(ctx.message.channel)
#		try:
#			mbr = ctx.message.mentions[0].id
#		except:
#			mbr = None
#		try:
#			t_pogo, t_cheat = c.execute('SELECT pogo_name, spoofer FROM trainers WHERE discord_id=? OR pogo_name=?', (mbr,mention)).fetchone()
#		except:
#			await self.bot.say("Error!")
#		else:
#			if t_cheat==1:
#				try:
#					c.execute('UPDATE trainers SET spoofer=? WHERE pogo_name=?', (0, t_pogo))
#				except sqlite3.IntegrityError:
#					await self.bot.say("Error!")
#				else:
#					await self.bot.say("Success! You've unset the `spoofer` flag on {}!".format(t_pogo))
#					trnr.commit()
#			else:
#				try:
#					c.execute('UPDATE trainers SET spoofer=?, spoofed=? WHERE pogo_name=?', (1,1, t_pogo))
#				except sqlite3.IntegrityError:
#					await self.bot.say("Error!")
#				else:
#					await self.bot.say("Success! You've set the `spoofer` flag on {}!".format(t_pogo))
#					trnr.commit()
#			await self.profileCard(t_pogo, ctx.message.channel)

	@commands.command(name="addprofile", no_pm=True, pass_context=True, alias="newprofile")
	@checks.mod_or_permissions(assign_roles=True)
	async def addprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""adding a user to the database"""
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = r.trainerLevels(level=level) + xp
		team = await self.getTeamByName(team)
		if opt.title() == 'Spoofer':
			await self._addProfile(mbr, name, xp, team.id, has_cheated=True, currently_cheats=True)
		else:
			await self._addProfile(mbr, name, xp, team.id)
		await self.profileCard(name)
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def addsecondary(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''):
		"""adding a trainer's second profile to the database"""
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = r.trainerLevels(level=level) + xp
		team = await self.getTeamByName(team)
		if opt.title() == 'Spoofer':
			await self._addProfile(mbr, name, xp, team.id, has_cheated=True, currently_cheats=True, prefered=False)
		else:
			await self._addProfile(mbr, name, xp, team.id, prefered=False)
		await self.profileCard(name)
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""applies the correct roles to a user and adds the user to the database"""
		await self.bot.send_typing(ctx.message.channel)
		xp = r.trainerLevels(level=level) + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.say("That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		mbr = ctx.message.mentions[0]
		try:
			await self.bot.change_nickname(mbr, name)
		except discord.errors.Forbidden:
			await self.bot.say("Error: I don't have permission to change nicknames. Aborted!")
		else:
			if (opt.title() in ['Minor', 'Child']) and discord.utils.get(ctx.message.server.roles, name='Minor'):
				approved_mentionable = discord.utils.get(ctx.message.server.roles, name='Minor')
			else:
				approved_mentionable = discord.utils.get(ctx.message.server.roles, name='Trainer')
			team_mentionable = discord.utils.get(ctx.message.server.roles, name=team.name)
			try:
				await self.bot.add_roles(mbr, approved_mentionable)
				if team_mentionable is not None:
					await asyncio.sleep(2.5) #Waits for 2.5 seconds to pass to get around Discord rate limiting
					await self.bot.add_roles(mbr, team_mentionable)
			except discord.errors.Forbidden:
				await self.bot.say("Error: I don't have permission to set roles. Aborted!")
			else:
				await self.bot.say("{} has been approved, super. They're probably super cool, be nice to them.".format(name))
				if opt.title() == 'Spoofer':
					await self._addProfile(mbr, name, xp, team.id, has_cheated=True, currently_cheats=True)
				else:
					await self._addProfile(mbr, name, xp, team.id)
				await self.profileCard(name)

	@commands.group(pass_context=True)
	@checks.is_owner()
	async def tdset(self, ctx):
		"""Settings for TrainerDex cog"""
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)

	@tdset.command(pass_context=True)
	@checks.is_owner()
	async def api(self, ctx, token: str):
		"""Sets the TrainerDex API token - owner only"""
		settings = dataIO.load_json(settings_file)
		if token:
			settings['token'] = token
			dataIO.save_json(settings_file, settings)
			await self.bot.say('```API token set```')
	
def check_folders():
	if not os.path.exists("data/trainerdex"):
		print("Creating data/trainerdex folder...")
		os.makedirs("data/trainerdex")
		
def check_file():
	f = 'data/trainerdex/settings.json'
	data = {}
	data['token'] = ''
	if not dataIO.is_valid_json(f):
		print("Creating default token.json...")
		dataIO.save_json(f, data)
	
def setup(bot):
	check_folders()
	check_file()
	importedTrainerDex = True
	bot.add_cog(TrainerDex(bot))