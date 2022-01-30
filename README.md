# Brownify
Brownify allows you to make your music brown. It splits audio tracks separate tracks for individual instruments, and it allows for performing basic modifications to those tracks. The tracks can then be recombined to help form a brown version of the original audio track.

## What is "brown" music?
In some ways, that is up to you! But the terminology at least comes from the band Ween.

Various people have expressed their opinion on what it means for music to be brown over on this [Ween subreddit thread](https://www.reddit.com/r/ween/comments/8etdtd/what_is_brown/), but one of the founding members of Ween summarized it in this way:
> I can’t really explain ‘brown’ except to give examples... Ween opened for The Ramones in 1991. The Ramones showed up in a Country Squire station wagon that was smashed on one side, and missing a window. Dee Dee, Joey, and Marky. That’s brown. The beautiful side of brown. That is brown – that’s real. That’s brown. It can be really bad, it can be a horrible thing, when you get browned out by some band. A band shows up and they’re brown – none of their equipment works or whatever. But it’s a strength. You know you’re getting the real thing.

## How does Brownify split audio tracks?
Brownify uses the [Spleeter](https://github.com/deezer/spleeter) library for this. Spleeter does the heavy lifting.

At this point in time, Brownify supports the 5-stem splitter, which splits songs into the following separate tracks:
 - Bass
 - Drums
 - Piano
 - Vocals
 - Other (i.e. everything else)

# Usage
In order to use Brownify, you can either use the python API or a command line program.

## What are Brownify recipes?
Brownify allows for user-specified modifications to audio tracks and a user-specified definition of how to merge audio tracks. To support his, Brownify relies on simple configurations called "recipes". Some example recipes are provided in the [recipes](./recipes) directory.

### Recipe syntax
Recipes are defined by a series of pipeline specifications. Each pipeline is comprised of a track source, a series of actions, and a track sink. Below is an example:
```
vocals -> flat -> early -> save(newVocals);
```

In this example, the vocals of the original audio track are made flat and a little bit early compared to the original audio. The resulting track is marked to be merged into the final track using the `save` wrapper around the sink.

Here is a more complicated example:
```
vocals -> octaveup -> early -> save(vocals1);
vocals -> octavedown -> late -> save(vocals2);
bass -> late -> late -> late -> late -> lateBass;
lateBass -> flat -> save(flatBass);
lateBass -> halfflat -> save(halfFlatBass);
drums -> save(drums);
other -> save(other);
piano -> save(piano);
```

In the above example, the original vocals are duplicted and modified. The original vocals are not part of the final track. A temporary sink called lateBass is defined and used to create two versions of teh bass track. Note that "lateBass" is not part of the final track, as it does not include the `save` wrapper around the sink. However, it is used to define two tracks `flatBass` and `halfFlatBass` which are saved as part of the final track.

When defining recipes, the following are available to you:

Original sources:
 - `bass`: The bass track split out by the audio splitter
 - `drums`: The drum track split out by the audio splitter
 - `other`: The track of remaining instruments split out by the audio splitter
 - `piano`: The piano track split out by the audio splitter
 - `vocals`: The vocal track split out by the audio splitter

Names:
Sinks must be named. Names are alpha-numeric with no punctuation or whitespace.

Defined sources:
A defined source is a named sink which was already defined in a previous pipeline.

Actions:
 - `early`: Make the audio slightly (but noticeably) early.
 - `flat`: Tune the audio pitch down by a full step.
 - `halfflat`: Tune the audio pitch down by a half step.
 - `halfsharp`: Tune the audio pitch up by a half step.
 - `late`: Make the audio slightly (but noticeably) late.
 - `octavedown`: Tune the audio pitch down by a full octave.
 - `octaveup`: Tune the audio pitch up by a full octave.
 - `sharp`: Tune the audio pitch up by a full step.

Sinks:
A sink must be named. It can either be temporary (to be used as a defined source) or part of the final track. Temporary sinks are useful for reusing sets of actions over a common audio source. In order to make a source temporary, it is simply named with no wrapper. To mark a sink as part of the final audio track, the name of the sink should be wrapped with the save wrapper, like this:
```
save(NAME)
```

More examples can be found in the [recipes](recipes) directory.

## Command line program
Coming soon.

### Examples
Coming soon.

## Python API
Coming soon.
