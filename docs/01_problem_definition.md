# Problem Definition

## Problem

In real companies, teams conduct many types of meetings every day, such as:

  * Sprint planning meetings   
  * Client meetings
  * Project review meetings
  * HR meetings
  * Technical discussions

A typical meeting may last 30–60 minutes. After the meeting ends, someone must remember and record:

  * What was discussed
  * What decisions were made
  * Who is responsible for each task
  * What the deadlines are

Currently, most organizations rely on manual note-taking and summary writing. This process has several limitations:

  * Important information can be lost
  * Writing summaries is time-consuming
  * Deadlines may be missed
  * Responsibilities may become unclear
  * Employees often waste time replaying meeting recordings to find specific information

As the number of meetings increases, managing meeting information becomes inefficient and difficult.

## Existing Solutions

Several commercial AI meeting assistants already exist, including Otter.ai, Fireflies.ai, Zoom AI Companion, and Microsoft Teams Copilot. These platforms provide features such as transcription and summarization.

However, this project is designed as an educational and engineering-focused implementation.

The objective is to understand and implement the architecture and engineering practices behind modern enterprise AI meeting intelligence systems, rather than to compete directly with commercial products.

## Users

  * Team leads
  * Managers
  * Developers
  * HR teams
  * Project coordinators

## AI Solution

This project aims to solve the following problem:

> How can we automatically convert a meeting conversation into useful, structured, and searchable business information?

The proposed AI Meeting Assistant consists of four main components:

  1. Audio → Text (Speech Recognition- whisper)
  2. Speaker Diarization(who spoke each part of the conversation)
  3. Meeting Intelligence (LLM Summarization)
  4. Searchable Meeting Knowledge Base (RAG)


## Success Metrics

  * Transcription accuracy > 90%
  * Summary quality - human should be able to understand the meeting without listening to the meeting
  * Action item extraction precision > 80% (at least 8 out of 10 assigned tasks should be extracted     successfully)
  * Processing time < 2x audio duration
  * For a user question, correct answers should be returned for approximately 85–90%

