# foresight

A League of Legends analytics platform that digs into match timeline data — not just the final scoreboard.

Most existing platforms show you end-of-game stats: KDA, CS, damage dealt. That's fine, but there's a lot more interesting stuff hiding in the timeline. When did that item spike actually kick in? Was that Trinity Force purchase good when you were 2k gold down? How does this champion's damage curve look at 15 vs 25 minutes?

That's what this project is trying to answer.

## What it does

Pulls data from the official Riot Games API (match history + match timeline endpoints) and stores it locally for analysis. From there, the goal is to build out metrics around:

- Item performance relative to gold state (ahead/behind/even)
- Champion scaling curves over game time
- Objective conversion and snowball/comeback patterns
- Game-state-aware build effectiveness
- Team composition dynamics over time

This is a personal project. It's not going to be a public service, won't touch anything Riot doesn't expose through their API, and won't provide any kind of in-game advantage or hidden information.

## Stack

| Layer | Choice |
|---|---|
| Language | Python |
| Data processing | Polars |
| Database | PostgreSQL |
| ORM / queries | SQLAlchemy or raw SQL |
| Notebooks | Jupyter |

## Setup

> Coming soon — project is in early stages.

You'll need a Riot API key (development key is fine for personal use) and a running PostgreSQL instance.

## Scope (for now)

- Ranked games only
- One or two regions
- Small dataset to start — expand if it turns out to be useful

## Notes

This project complies with [Riot's API terms of service](https://developer.riotgames.com/policies/general). It only uses publicly available post-game match and timeline data.
